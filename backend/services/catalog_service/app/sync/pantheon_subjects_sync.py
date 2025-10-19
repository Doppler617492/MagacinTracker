"""
Pantheon Subjects Sync Service
Synchronizes partners/subjects from Pantheon ERP via GetSubjectWMS endpoint
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.logging import get_logger
from app_common.pantheon_client import PantheonAPIClient
from app_common.pantheon_config import pantheon_config

logger = get_logger(__name__)


class PantheonSubjectsSyncService:
    """
    Subjects/Partners sync service with type classification
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "total_fetched": 0,
            "subjects_created": 0,
            "subjects_updated": 0,
            "subjects_marked_inactive": 0,
            "by_type": {"supplier": 0, "customer": 0, "warehouse": 0},
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    def _classify_subject_type(self, subject_data: Dict[str, Any]) -> str:
        """
        Classify subject type based on Pantheon data
        Rules:
        - If has warehouse code → warehouse
        - If is_supplier flag → supplier
        - Otherwise → customer
        """
        # Check for explicit type field
        if "type" in subject_data:
            return subject_data["type"].lower()
        
        # Check warehouse indicators
        if subject_data.get("magacin") or subject_data.get("warehouse_code"):
            return "warehouse"
        
        # Check supplier flag
        if subject_data.get("is_dobavljac") or subject_data.get("is_supplier"):
            return "supplier"
        
        # Default to customer
        return "customer"
    
    async def upsert_subject(self, subject_data: Dict[str, Any]) -> Optional[str]:
        """Upsert subject into database"""
        try:
            from task_service.app.models import Subject
            from task_service.app.models.enums import SubjectType
            
            code = subject_data.get("sifra") or subject_data.get("code")
            if not code:
                logger.warning(f"Subject missing code: {subject_data}")
                self.stats["errors"] += 1
                return None
            
            # Check if subject exists
            result = await self.session.execute(
                select(Subject).where(Subject.code == code)
            )
            subject = result.scalar_one_or_none()
            
            # Classify type
            subject_type_str = self._classify_subject_type(subject_data)
            subject_type = SubjectType(subject_type_str)
            
            # Prepare data
            subject_dict = {
                "name": subject_data.get("naziv") or subject_data.get("name", ""),
                "type": subject_type,
                "pib": subject_data.get("pib"),
                "address": subject_data.get("adresa") or subject_data.get("address"),
                "city": subject_data.get("grad") or subject_data.get("city"),
                "postal_code": subject_data.get("postanski_broj") or subject_data.get("postal_code"),
                "country": subject_data.get("drzava") or subject_data.get("country", "RS"),
                "phone": subject_data.get("telefon") or subject_data.get("phone"),
                "email": subject_data.get("email"),
                "time_chg_ts": self._parse_timestamp(subject_data.get("adTimeChg")),
                "last_synced_at": datetime.utcnow(),
                "source": "PANTHEON",
                "aktivan": True
            }
            
            if subject:
                # Update existing
                for key, value in subject_dict.items():
                    setattr(subject, key, value)
                self.stats["subjects_updated"] += 1
                logger.debug(f"Updated subject: {code}")
            else:
                # Create new
                subject = Subject(code=code, **subject_dict)
                self.session.add(subject)
                self.stats["subjects_created"] += 1
                logger.info(f"Created subject: {code} (type={subject_type_str})")
            
            self.stats["by_type"][subject_type_str] += 1
            await self.session.flush()
            return str(subject.id)
            
        except Exception as e:
            logger.error(f"Failed to upsert subject {subject_data.get('sifra')}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def mark_inactive_subjects(self, synced_codes: set):
        """Mark subjects as inactive if not updated"""
        try:
            from task_service.app.models import Subject
            
            cutoff_date = datetime.utcnow() - timedelta(days=pantheon_config.delta_window_days * 2)
            
            result = await self.session.execute(
                update(Subject)
                .where(
                    Subject.source == "PANTHEON",
                    Subject.code.notin_(synced_codes),
                    Subject.last_synced_at < cutoff_date,
                    Subject.aktivan == True
                )
                .values(aktivan=False)
                .execution_options(synchronize_session=False)
            )
            
            count = result.rowcount
            self.stats["subjects_marked_inactive"] = count
            
            if count > 0:
                logger.info(f"Marked {count} subjects as inactive")
            
        except Exception as e:
            logger.error(f"Failed to mark inactive subjects: {e}")
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Pantheon timestamp"""
        if not timestamp_str:
            return None
        try:
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                return datetime.fromisoformat(timestamp_str)
            except:
                return None
    
    async def sync_subjects(self, full_sync: bool = False) -> Dict[str, Any]:
        """Main sync method for subjects"""
        self.stats["start_time"] = datetime.utcnow()
        logger.info(f"🔄 Starting Pantheon subjects sync (full_sync={full_sync})")
        
        try:
            # Connect to Pantheon API
            async with PantheonAPIClient() as client:
                synced_codes = set()
                offset = 0
                page_limit = pantheon_config.page_limit
                
                while True:
                    logger.debug(f"Fetching subjects: offset={offset}, limit={page_limit}")
                    
                    response = await client.get_subject_wms(
                        limit=page_limit,
                        offset=offset
                    )
                    
                    if not response or "items" not in response:
                        break
                    
                    items = response.get("items", [])
                    if not items:
                        break
                    
                    logger.info(f"Processing {len(items)} subjects (offset={offset})")
                    
                    for subject_data in items:
                        subject_id = await self.upsert_subject(subject_data)
                        if subject_id:
                            code = subject_data.get("sifra") or subject_data.get("code")
                            synced_codes.add(code)
                        self.stats["total_fetched"] += 1
                    
                    await self.session.commit()
                    
                    total = response.get("total", 0)
                    if offset + page_limit >= total:
                        break
                    
                    offset += page_limit
                
                # Mark inactive
                if full_sync or len(synced_codes) > 50:
                    await self.mark_inactive_subjects(synced_codes)
                
            self.stats["end_time"] = datetime.utcnow()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info(
                f"✅ Subjects sync completed in {duration:.2f}s: "
                f"{self.stats['total_fetched']} fetched, "
                f"{self.stats['subjects_created']} created, "
                f"{self.stats['subjects_updated']} updated, "
                f"by_type={self.stats['by_type']}"
            )
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Subjects sync failed: {e}", exc_info=True)
            self.stats["end_time"] = datetime.utcnow()
            self.stats["status"] = "failed"
            return self.stats


async def sync_pantheon_subjects(
    session: AsyncSession,
    full_sync: bool = False
) -> Dict[str, Any]:
    """Public API for syncing subjects from Pantheon"""
    service = PantheonSubjectsSyncService(session)
    return await service.sync_subjects(full_sync=full_sync)

