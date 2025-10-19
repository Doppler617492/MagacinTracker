"""
Pantheon Catalog Sync Service
Synchronizes articles and barcodes from Pantheon ERP via getIdentWMS endpoint
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.logging import get_logger
from app_common.pantheon_client import PantheonAPIClient
from app_common.pantheon_config import pantheon_config

logger = get_logger(__name__)


class PantheonCatalogSyncService:
    """
    Enterprise-grade catalog sync service with:
    - Delta sync based on time_chg_ts
    - Pagination (1000 items/page)
    - Upsert logic for articles and barcodes
    - Inactive article marking
    - Detailed metrics and logging
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.stats = {
            "total_fetched": 0,
            "articles_created": 0,
            "articles_updated": 0,
            "articles_marked_inactive": 0,
            "barcodes_created": 0,
            "barcodes_updated": 0,
            "errors": 0,
            "start_time": None,
            "end_time": None
        }
    
    async def get_last_sync_timestamp(self) -> Optional[datetime]:
        """Get the last successful sync timestamp from database"""
        try:
            # Import models locally to avoid circular imports
            from task_service.app.models import CatalogSyncStatus
            
            result = await self.session.execute(
                select(CatalogSyncStatus.last_sync_ts)
                .where(CatalogSyncStatus.sync_type == "PANTHEON_CATALOG")
                .order_by(CatalogSyncStatus.last_sync_ts.desc())
                .limit(1)
            )
            row = result.scalar_one_or_none()
            return row
            
        except Exception as e:
            logger.warning(f"Could not fetch last sync timestamp: {e}")
            # Fallback: sync last N days
            return datetime.utcnow() - timedelta(days=pantheon_config.delta_window_days)
    
    async def save_last_sync_timestamp(self, timestamp: datetime):
        """Save the sync timestamp"""
        try:
            from task_service.app.models import CatalogSyncStatus
            
            sync_status = CatalogSyncStatus(
                sync_type="PANTHEON_CATALOG",
                last_sync_ts=timestamp,
                items_synced=self.stats["total_fetched"],
                status="completed"
            )
            self.session.add(sync_status)
            await self.session.commit()
            
        except Exception as e:
            logger.error(f"Failed to save sync timestamp: {e}")
    
    async def upsert_article(self, article_data: Dict[str, Any]) -> Optional[str]:
        """
        Upsert article into database
        Returns: article_id (UUID as string) or None
        """
        try:
            from task_service.app.models import Artikal
            
            # CORRECTED: Pantheon field names are Ident, Naziv, JM, etc. (capitalized)
            code = article_data.get("Ident") or article_data.get("sifra") or article_data.get("code")
            if not code or code.strip() == "":
                logger.warning(f"Article missing code: {article_data}")
                self.stats["errors"] += 1
                return None
            
            # Check if article exists
            result = await self.session.execute(
                select(Artikal).where(Artikal.sifra == code)
            )
            article = result.scalar_one_or_none()
            
            # Prepare data (map Pantheon fields)
            article_dict = {
                "naziv": article_data.get("Naziv") or article_data.get("naziv") or "",
                "jedinica_mjere": article_data.get("JM") or article_data.get("jedinica_mjere") or "kom",
                "supplier": article_data.get("Dobavljac") or article_data.get("dobavljac"),
                "article_class": article_data.get("PrimKlasif") or article_data.get("klasa"),
                "description": article_data.get("Opis") or article_data.get("opis"),
                "time_chg_ts": self._parse_timestamp(article_data.get("adTimeChg")),
                "last_synced_at": datetime.utcnow(),
                "source": "PANTHEON",
                "aktivan": article_data.get("Aktivan", "T") == "T"  # T=true, F=false
            }
            
            if article:
                # Update existing
                for key, value in article_dict.items():
                    setattr(article, key, value)
                self.stats["articles_updated"] += 1
                logger.debug(f"Updated article: {code}")
            else:
                # Create new
                article = Artikal(sifra=code, **article_dict)
                self.session.add(article)
                self.stats["articles_created"] += 1
                logger.info(f"Created article: {code}")
            
            await self.session.flush()
            return str(article.id)
            
        except Exception as e:
            logger.error(f"Failed to upsert article {article_data.get('sifra')}: {e}")
            self.stats["errors"] += 1
            return None
    
    async def upsert_barcodes(self, article_id: str, barcodes_data: List[str]):
        """Upsert barcodes for an article"""
        try:
            from task_service.app.models import ArtikalBarkod
            import uuid
            
            article_uuid = uuid.UUID(article_id)
            
            for barcode_value in barcodes_data:
                if not barcode_value:
                    continue
                
                # Check if barcode exists
                result = await self.session.execute(
                    select(ArtikalBarkod).where(ArtikalBarkod.barkod == barcode_value)
                )
                barcode = result.scalar_one_or_none()
                
                if barcode:
                    # Update association if needed
                    if barcode.artikal_id != article_uuid:
                        barcode.artikal_id = article_uuid
                        self.stats["barcodes_updated"] += 1
                else:
                    # Create new barcode
                    barcode = ArtikalBarkod(
                        artikal_id=article_uuid,
                        barkod=barcode_value,
                        is_primary=(barcodes_data.index(barcode_value) == 0)
                    )
                    self.session.add(barcode)
                    self.stats["barcodes_created"] += 1
            
            await self.session.flush()
            
        except Exception as e:
            logger.error(f"Failed to upsert barcodes for article {article_id}: {e}")
            self.stats["errors"] += 1
    
    async def mark_inactive_articles(self, synced_codes: set):
        """Mark articles as inactive if not updated in N days"""
        try:
            from task_service.app.models import Artikal
            
            cutoff_date = datetime.utcnow() - timedelta(days=pantheon_config.delta_window_days * 2)
            
            result = await self.session.execute(
                update(Artikal)
                .where(
                    Artikal.source == "PANTHEON",
                    Artikal.sifra.notin_(synced_codes),
                    Artikal.last_synced_at < cutoff_date,
                    Artikal.aktivan == True
                )
                .values(aktivan=False)
                .execution_options(synchronize_session=False)
            )
            
            count = result.rowcount
            self.stats["articles_marked_inactive"] = count
            
            if count > 0:
                logger.info(f"Marked {count} articles as inactive")
            
        except Exception as e:
            logger.error(f"Failed to mark inactive articles: {e}")
    
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Pantheon timestamp string to datetime"""
        if not timestamp_str:
            return None
        
        try:
            # Pantheon format: YYYY-MM-DD HH:MM:SS
            return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        except:
            try:
                # Alternative format: ISO 8601
                return datetime.fromisoformat(timestamp_str)
            except:
                logger.warning(f"Could not parse timestamp: {timestamp_str}")
                return None
    
    async def sync_catalog(self, full_sync: bool = False) -> Dict[str, Any]:
        """
        Main sync method - fetches articles from Pantheon and syncs to database
        
        Args:
            full_sync: If True, sync all articles; if False, delta sync only
        
        Returns:
            Dictionary with sync statistics
        """
        self.stats["start_time"] = datetime.utcnow()
        logger.info(f"🔄 Starting Pantheon catalog sync (full_sync={full_sync})")
        
        try:
            # Get last sync timestamp for delta sync
            last_sync_ts = None if full_sync else await self.get_last_sync_timestamp()
            
            if last_sync_ts:
                timestamp_str = last_sync_ts.strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"Delta sync from: {timestamp_str}")
            else:
                logger.info("Full sync requested or no previous sync found")
            
            # Connect to Pantheon API
            async with PantheonAPIClient() as client:
                synced_codes = set()
                offset = 0
                page_limit = pantheon_config.page_limit
                
                while True:
                    # Fetch page from Pantheon
                    logger.debug(f"Fetching page: offset={offset}, limit={page_limit}")
                    
                    response = await client.get_ident_wms(
                        ad_time_chg=timestamp_str if last_sync_ts else None,
                        limit=page_limit,
                        offset=offset
                    )
                    
                    if not response or "items" not in response:
                        logger.warning("No data returned from Pantheon")
                        break
                    
                    items = response.get("items", [])
                    if not items:
                        logger.info("No more items to sync")
                        break
                    
                    logger.info(f"Processing {len(items)} articles (offset={offset})")
                    
                    # Process each article
                    for article_data in items:
                        # Upsert article
                        article_id = await self.upsert_article(article_data)
                        
                        if article_id:
                            code = article_data.get("Ident") or article_data.get("sifra") or article_data.get("code")
                            synced_codes.add(code)
                            
                            # Upsert barcodes (Pantheon returns array of {"Barkod": "..."})
                            barcodes_data = article_data.get("Barkodovi") or article_data.get("barkodovi") or []
                            barcodes = [b.get("Barkod") or b for b in barcodes_data if b]
                            if barcodes:
                                await self.upsert_barcodes(article_id, barcodes)
                        
                        self.stats["total_fetched"] += 1
                    
                    # Commit batch
                    await self.session.commit()
                    
                    # Check if we have more pages
                    total = response.get("total", 0)
                    if offset + page_limit >= total:
                        break
                    
                    offset += page_limit
                
                # Mark inactive articles (only for full sync or large delta)
                if full_sync or len(synced_codes) > 100:
                    await self.mark_inactive_articles(synced_codes)
                
                # Save sync timestamp
                await self.save_last_sync_timestamp(datetime.utcnow())
                
            self.stats["end_time"] = datetime.utcnow()
            duration = (self.stats["end_time"] - self.stats["start_time"]).total_seconds()
            
            logger.info(
                f"✅ Catalog sync completed in {duration:.2f}s: "
                f"{self.stats['total_fetched']} fetched, "
                f"{self.stats['articles_created']} created, "
                f"{self.stats['articles_updated']} updated, "
                f"{self.stats['barcodes_created']} barcodes created, "
                f"{self.stats['errors']} errors"
            )
            
            return self.stats
            
        except Exception as e:
            logger.error(f"❌ Catalog sync failed: {e}", exc_info=True)
            self.stats["end_time"] = datetime.utcnow()
            self.stats["status"] = "failed"
            self.stats["error"] = str(e)
            return self.stats


# =========================================================================
# PUBLIC API
# =========================================================================

async def sync_pantheon_catalog(
    session: AsyncSession,
    full_sync: bool = False
) -> Dict[str, Any]:
    """
    Public API for syncing catalog from Pantheon
    
    Args:
        session: AsyncSession for database
        full_sync: If True, sync all articles; if False, delta sync
    
    Returns:
        Sync statistics dictionary
    """
    service = PantheonCatalogSyncService(session)
    return await service.sync_catalog(full_sync=full_sync)

