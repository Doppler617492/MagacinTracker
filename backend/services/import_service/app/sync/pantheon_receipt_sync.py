"""
Pantheon Receipt (Inbound) Sync Service
Synchronizes inbound documents from Pantheon ERP via GetReceiptDocWMS endpoint
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.logging import get_logger
from app_common.pantheon_client import PantheonAPIClient
from app_common.pantheon_config import pantheon_config

logger = get_logger(__name__)


class PantheonReceiptSyncService:
    """
    Inbound/Receipt documents sync service
    (Similar to Dispatch sync but for inbound documents)
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "total_docs": 0,
            "docs_created": 0,
            "docs_updated": 0,
            "total_items": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def upsert_receipt(
        self,
        doc_data: Dict[str, Any]
    ) -> Optional[UUID]:
        """Upsert receipt document and items"""
        try:
            from task_service.app.models import Receipt, ReceiptItem, DocType
            from task_service.app.models.enums import DocumentDirection, DocumentItemStatus
            from import_service.app.sync.pantheon_dispatch_sync import PantheonDispatchSyncService
            
            doc_no = doc_data.get("doc_no") or doc_data.get("dokumentBroj")
            doc_date_str = doc_data.get("date") or doc_data.get("datum")
            doc_type_code = doc_data.get("doc_type") or doc_data.get("tipDokumenta", "UNKNOWN")
            
            if not doc_no or not doc_date_str:
                logger.warning(f"Receipt missing doc_no or date")
                self.stats["errors"] += 1
                return None
            
            # Parse date
            try:
                if isinstance(doc_date_str, str):
                    doc_date = datetime.strptime(doc_date_str.split()[0], "%Y-%m-%d").date()
                else:
                    doc_date = doc_date_str
            except:
                doc_date = date.today()
            
            # Upsert doc type
            result = await self.session.execute(
                select(DocType).where(DocType.code == doc_type_code)
            )
            doc_type = result.scalar_one_or_none()
            
            if not doc_type:
                doc_type = DocType(
                    code=doc_type_code,
                    name=doc_data.get("doc_type_name", doc_type_code),
                    direction=DocumentDirection.INBOUND
                )
                self.session.add(doc_type)
                await self.session.flush()
            
            # Check if receipt exists
            result = await self.session.execute(
                select(Receipt).where(
                    Receipt.doc_no == doc_no,
                    Receipt.doc_type_id == doc_type.id,
                    Receipt.date == doc_date
                )
            )
            receipt = result.scalar_one_or_none()
            
            receipt_dict = {
                "responsible_person": doc_data.get("responsible_person"),
                "header_ref": doc_data.get("header_ref"),
                "notes": doc_data.get("notes"),
                "last_synced_at": datetime.utcnow()
            }
            
            if receipt:
                for key, value in receipt_dict.items():
                    setattr(receipt, key, value)
                self.stats["docs_updated"] += 1
                
                # Delete old items
                await self.session.execute(
                    ReceiptItem.__table__.delete().where(ReceiptItem.receipt_id == receipt.id)
                )
            else:
                receipt = Receipt(
                    doc_no=doc_no,
                    doc_type_id=doc_type.id,
                    date=doc_date,
                    **receipt_dict
                )
                self.session.add(receipt)
                self.stats["docs_created"] += 1
            
            await self.session.flush()
            
            # Process items (no WMS filtering for receipts - receive everything)
            items_data = doc_data.get("items", [])
            
            for item_data in items_data:
                receipt_item = ReceiptItem(
                    receipt_id=receipt.id,
                    code=item_data.get("sifra") or item_data.get("code", ""),
                    name=item_data.get("naziv") or item_data.get("name", ""),
                    unit=item_data.get("jedinica_mjere") or item_data.get("unit", "kom"),
                    barcode=item_data.get("barkod") or item_data.get("barcode"),
                    qty_requested=Decimal(str(item_data.get("kolicina_trazena", 0))),
                    qty_completed=Decimal(str(item_data.get("kolicina_obradjena", 0))),
                    status=DocumentItemStatus.NEW
                )
                self.session.add(receipt_item)
                self.stats["total_items"] += 1
            
            await self.session.flush()
            return receipt.id
            
        except Exception as e:
            logger.error(f"Failed to upsert receipt: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None
    
    async def sync_receipts(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Main sync method"""
        self.stats["start_time"] = datetime.utcnow()
        
        if not date_from:
            date_from = (datetime.utcnow() - timedelta(hours=2)).date()
        if not date_to:
            date_to = datetime.utcnow().date()
        
        logger.info(f"🔄 Starting Pantheon receipt sync: {date_from} to {date_to}")
        
        try:
            async with PantheonAPIClient() as client:
                offset = 0
                page_limit = pantheon_config.page_limit
                
                while True:
                    response = await client.get_receipt_doc_wms(
                        date_from=date_from.isoformat(),
                        date_to=date_to.isoformat(),
                        limit=page_limit,
                        offset=offset
                    )
                    
                    if not response or "items" not in response:
                        break
                    
                    docs = response.get("items", [])
                    if not docs:
                        break
                    
                    logger.info(f"Processing {len(docs)} receipt documents (offset={offset})")
                    
                    for doc_data in docs:
                        await self.upsert_receipt(doc_data)
                        self.stats["total_docs"] += 1
                    
                    await self.session.commit()
                    
                    total = response.get("total", 0)
                    if offset + page_limit >= total:
                        break
                    
                    offset += page_limit
                
            self.stats["end_time"] = datetime.utcnow()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info(
                f"✅ Receipt sync completed in {duration:.2f}s: "
                f"{self.stats['total_docs']} docs, "
                f"{self.stats['total_items']} items"
            )
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Receipt sync failed: {e}", exc_info=True)
            self.stats["status"] = "failed"
            return self.stats


async def sync_pantheon_receipts(
    session: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict[str, Any]:
    """Public API"""
    service = PantheonReceiptSyncService(session)
    return await service.sync_receipts(date_from=date_from, date_to=date_to)

