"""
Pantheon Dispatch (Outbound/Issue) Sync Service
Synchronizes outbound documents from Pantheon ERP via GetIssueDocWMS endpoint
CRITICAL: Implements exists_in_wms logic for WMS task creation
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.logging import get_logger
from app_common.pantheon_client import PantheonAPIClient
from app_common.pantheon_config import pantheon_config

logger = get_logger(__name__)


class PantheonDispatchSyncService:
    """
    Outbound/Issue documents sync with WMS filtering logic
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "total_docs": 0,
            "docs_created": 0,
            "docs_updated": 0,
            "total_items": 0,
            "items_exists_in_wms": 0,
            "items_not_in_wms": 0,
            "article_lookups": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def lookup_article_by_code(self, code: str) -> Optional[UUID]:
        """
        Lookup article in database by code
        Returns: article_id (UUID) or None
        """
        try:
            from task_service.app.models import Artikal
            
            result = await self.session.execute(
                select(Artikal.id).where(Artikal.sifra == code, Artikal.aktivan == True)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to lookup article {code}: {e}")
            return None
    
    async def lookup_article_by_barcode(self, barcode: str) -> Optional[UUID]:
        """Lookup article by barcode"""
        try:
            from task_service.app.models import ArtikalBarkod
            
            result = await self.session.execute(
                select(ArtikalBarkod.artikal_id).where(ArtikalBarkod.barkod == barcode)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to lookup barcode {barcode}: {e}")
            return None
    
    async def on_demand_article_lookup(
        self,
        code: str,
        client: PantheonAPIClient
    ) -> Optional[UUID]:
        """
        On-demand article lookup via Pantheon API
        If article not in local DB, fetch from Pantheon and create
        """
        try:
            logger.info(f"🔍 On-demand lookup for article: {code}")
            self.stats["article_lookups"] += 1
            
            # Fetch from Pantheon
            response = await client.get_ident_wms(limit=1, offset=0)
            # TODO: Add filter by code when Pantheon supports it
            
            if not response or "items" not in response:
                logger.warning(f"No data from Pantheon for article {code}")
                return None
            
            items = response.get("items", [])
            if not items:
                return None
            
            # Find matching article
            article_data = next((item for item in items if item.get("sifra") == code), None)
            if not article_data:
                return None
            
            # Import article using catalog sync
            from catalog_service.app.sync.pantheon_catalog_sync import PantheonCatalogSyncService
            sync_service = PantheonCatalogSyncService(self.session)
            article_id = await sync_service.upsert_article(article_data)
            
            if article_id:
                # Handle barcodes
                barcodes = article_data.get("barkodovi") or article_data.get("barcodes", [])
                if barcodes:
                    await sync_service.upsert_barcodes(article_id, barcodes)
                
                await self.session.commit()
                logger.info(f"✅ Created article {code} via on-demand lookup")
            
            return UUID(article_id) if article_id else None
            
        except Exception as e:
            logger.error(f"On-demand lookup failed for {code}: {e}")
            return None
    
    async def resolve_article(
        self,
        item_data: Dict[str, Any],
        client: PantheonAPIClient,
        enable_on_demand: bool = True
    ) -> Optional[UUID]:
        """
        Resolve article_id from item data
        Tries: 1) code, 2) barcode, 3) on-demand lookup
        """
        code = item_data.get("sifra") or item_data.get("code")
        barcode = item_data.get("barkod") or item_data.get("barcode")
        
        # Try by code first
        if code:
            article_id = await self.lookup_article_by_code(code)
            if article_id:
                return article_id
        
        # Try by barcode
        if barcode:
            article_id = await self.lookup_article_by_barcode(barcode)
            if article_id:
                return article_id
        
        # On-demand lookup (if enabled)
        if enable_on_demand and code:
            article_id = await self.on_demand_article_lookup(code, client)
            if article_id:
                return article_id
        
        return None
    
    async def check_exists_in_wms(
        self,
        article_id: Optional[UUID],
        warehouse_code: Optional[str]
    ) -> bool:
        """
        CRITICAL BUSINESS LOGIC: Determine if item should create WMS task
        
        Rules:
        1. article_id must exist (matched in catalog)
        2. warehouse_code must match WMS_MAGACIN_CODE
        
        Returns: True if eligible for WMS, False otherwise
        """
        if not article_id:
            return False
        
        if not warehouse_code:
            return False
        
        # Check if warehouse matches our WMS warehouse
        if warehouse_code != pantheon_config.wms_magacin_code:
            return False
        
        return True
    
    async def upsert_doc_type(self, doc_type_code: str, doc_type_name: str) -> UUID:
        """Upsert document type"""
        try:
            from task_service.app.models import DocType
            from task_service.app.models.enums import DocumentDirection
            
            result = await self.session.execute(
                select(DocType).where(DocType.code == doc_type_code)
            )
            doc_type = result.scalar_one_or_none()
            
            if not doc_type:
                doc_type = DocType(
                    code=doc_type_code,
                    name=doc_type_name,
                    direction=DocumentDirection.OUTBOUND
                )
                self.session.add(doc_type)
                await self.session.flush()
            
            return doc_type.id
        except Exception as e:
            logger.error(f"Failed to upsert doc_type {doc_type_code}: {e}")
            raise
    
    async def upsert_dispatch(
        self,
        doc_data: Dict[str, Any],
        client: PantheonAPIClient
    ) -> Optional[UUID]:
        """Upsert dispatch document and items"""
        try:
            from task_service.app.models import Dispatch, DispatchItem
            from task_service.app.models.enums import DocumentItemStatus
            
            doc_no = doc_data.get("doc_no") or doc_data.get("dokumentBroj")
            doc_date_str = doc_data.get("date") or doc_data.get("datum")
            doc_type_code = doc_data.get("doc_type") or doc_data.get("tipDokumenta", "UNKNOWN")
            
            if not doc_no or not doc_date_str:
                logger.warning(f"Dispatch missing doc_no or date: {doc_data}")
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
            doc_type_name = doc_data.get("doc_type_name", doc_type_code)
            doc_type_id = await self.upsert_doc_type(doc_type_code, doc_type_name)
            
            # Check if dispatch exists (unique: doc_no + doc_type_id + date)
            result = await self.session.execute(
                select(Dispatch).where(
                    Dispatch.doc_no == doc_no,
                    Dispatch.doc_type_id == doc_type_id,
                    Dispatch.date == doc_date
                )
            )
            dispatch = result.scalar_one_or_none()
            
            # Prepare data
            dispatch_dict = {
                "issuer": doc_data.get("issuer") or doc_data.get("izdavalac"),
                "receiver": doc_data.get("receiver") or doc_data.get("primalac"),
                "responsible_person": doc_data.get("responsible_person") or doc_data.get("odgovorno_lice"),
                "header_ref": doc_data.get("header_ref"),
                "notes": doc_data.get("notes") or doc_data.get("napomene"),
                "last_synced_at": datetime.utcnow()
            }
            
            if dispatch:
                # Update existing
                for key, value in dispatch_dict.items():
                    setattr(dispatch, key, value)
                self.stats["docs_updated"] += 1
                
                # Delete old items (will re-create)
                await self.session.execute(
                    DispatchItem.__table__.delete().where(DispatchItem.dispatch_id == dispatch.id)
                )
            else:
                # Create new
                dispatch = Dispatch(
                    doc_no=doc_no,
                    doc_type_id=doc_type_id,
                    date=doc_date,
                    **dispatch_dict
                )
                self.session.add(dispatch)
                self.stats["docs_created"] += 1
            
            await self.session.flush()
            
            # Process items
            items_data = doc_data.get("items", [])
            warehouse_code = doc_data.get("warehouse_code") or doc_data.get("magacin", pantheon_config.wms_magacin_code)
            
            for item_data in items_data:
                # Resolve article
                article_id = await self.resolve_article(item_data, client, enable_on_demand=True)
                
                # Check exists_in_wms
                exists_in_wms = await self.check_exists_in_wms(article_id, warehouse_code)
                
                if exists_in_wms:
                    self.stats["items_exists_in_wms"] += 1
                else:
                    self.stats["items_not_in_wms"] += 1
                
                # Create item
                dispatch_item = DispatchItem(
                    dispatch_id=dispatch.id,
                    article_id=article_id,
                    code=item_data.get("sifra") or item_data.get("code", ""),
                    name=item_data.get("naziv") or item_data.get("name", ""),
                    unit=item_data.get("jedinica_mjere") or item_data.get("unit", "kom"),
                    barcode=item_data.get("barkod") or item_data.get("barcode"),
                    qty_requested=Decimal(str(item_data.get("kolicina_trazena", 0))),
                    qty_completed=Decimal(str(item_data.get("kolicina_obradjena", 0))),
                    exists_in_wms=exists_in_wms,
                    wms_flag=exists_in_wms,  # Same as exists_in_wms for now
                    warehouse_code=warehouse_code,
                    status=DocumentItemStatus.NEW
                )
                self.session.add(dispatch_item)
                self.stats["total_items"] += 1
            
            await self.session.flush()
            return dispatch.id
            
        except Exception as e:
            logger.error(f"Failed to upsert dispatch {doc_data.get('doc_no')}: {e}", exc_info=True)
            self.stats["errors"] += 1
            return None
    
    async def sync_dispatches(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Main sync method for dispatches"""
        self.stats["start_time"] = datetime.utcnow()
        
        # Default: last 2 hours
        if not date_from:
            date_from = (datetime.utcnow() - timedelta(hours=2)).date()
        if not date_to:
            date_to = datetime.utcnow().date()
        
        logger.info(f"🔄 Starting Pantheon dispatch sync: {date_from} to {date_to}")
        
        try:
            async with PantheonAPIClient() as client:
                offset = 0
                page_limit = pantheon_config.page_limit
                
                while True:
                    response = await client.get_issue_doc_wms(
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
                    
                    logger.info(f"Processing {len(docs)} dispatch documents (offset={offset})")
                    
                    for doc_data in docs:
                        await self.upsert_dispatch(doc_data, client)
                        self.stats["total_docs"] += 1
                    
                    await self.session.commit()
                    
                    total = response.get("total", 0)
                    if offset + page_limit >= total:
                        break
                    
                    offset += page_limit
                
            self.stats["end_time"] = datetime.utcnow()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info(
                f"✅ Dispatch sync completed in {duration:.2f}s: "
                f"{self.stats['total_docs']} docs, "
                f"{self.stats['total_items']} items, "
                f"{self.stats['items_exists_in_wms']} WMS-eligible, "
                f"{self.stats['items_not_in_wms']} non-WMS"
            )
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Dispatch sync failed: {e}", exc_info=True)
            self.stats["status"] = "failed"
            return self.stats


async def sync_pantheon_dispatches(
    session: AsyncSession,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None
) -> Dict[str, Any]:
    """Public API for syncing dispatches"""
    service = PantheonDispatchSyncService(session)
    return await service.sync_dispatches(date_from=date_from, date_to=date_to)

