"""
Backfill script to populate catalog from existing trebovanje_stavka records.
This script reads all unique articles from trebovanje_stavka and creates them in the artikal table.

Usage:
    docker compose exec task-service python -m app.scripts.backfill_catalog
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine

from app_common.logging import get_logger

from ..config import settings
from ..models import Artikal, TrebovanjeStavka

logger = get_logger(__name__)


async def main():
    """Main backfill logic."""
    logger.info("backfill.start")
    
    # Create database engine
    engine = create_async_engine(settings.database_url, echo=False)
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy.orm import sessionmaker
        
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        async with async_session() as session:
            # Step 1: Load all unique articles from trebovanje_stavka
            logger.info("backfill.load_stavke")
            stmt = select(TrebovanjeStavka).order_by(TrebovanjeStavka.artikl_sifra)
            result = await session.execute(stmt)
            all_stavke = result.scalars().all()
            
            if not all_stavke:
                logger.info("backfill.no_stavke_found")
                print("No trebovanje stavke found in database.")
                return
            
            logger.info("backfill.grouping", total_stavke=len(all_stavke))
            
            # Group by sifra to get unique articles
            articles_by_sifra = defaultdict(list)
            for stavka in all_stavke:
                articles_by_sifra[stavka.artikl_sifra].append(stavka)
            
            logger.info("backfill.unique_articles", unique=len(articles_by_sifra))
            
            # Step 2: Load existing articles from catalog
            logger.info("backfill.load_existing_catalog")
            existing_stmt = select(Artikal)
            existing_result = await session.execute(existing_stmt)
            existing_artikli = {a.sifra: a for a in existing_result.scalars().all()}
            
            logger.info("backfill.existing_catalog", count=len(existing_artikli))
            
            # Step 3: Create new articles
            created = 0
            skipped = 0
            
            for sifra, stavke in articles_by_sifra.items():
                # Skip if already exists in catalog
                if sifra in existing_artikli:
                    skipped += 1
                    continue
                
                # Use the first stavka as the source of truth
                first_stavka = stavke[0]
                
                # Create article without barkodi (we don't have them populated anyway)
                artikal = Artikal(
                    id=uuid.uuid4(),
                    sifra=sifra,
                    naziv=first_stavka.naziv,
                    jedinica_mjere="kom",
                    aktivan=True,
                )
                session.add(artikal)
                created += 1
                existing_artikli[sifra] = artikal
            
            if created == 0:
                logger.info("backfill.no_new_articles", skipped=skipped)
                print(f"All {len(articles_by_sifra)} unique articles already exist in catalog.")
                return
            
            logger.info("backfill.creating", count=created, skipped=skipped)
            print(f"Creating {created} new articles in catalog (skipped {skipped} existing)")
            
            # Commit new articles
            await session.commit()
            
            logger.info("backfill.created", count=created)
            print(f"✅ Created {created} articles successfully!")
            
            # Step 4: Update trebovanje_stavka to link to articles
            logger.info("backfill.linking_stavke")
            print(f"\nLinking trebovanje_stavka records to catalog articles...")
            
            linked = 0
            for stavka in all_stavke:
                if stavka.artikal_id is None and stavka.artikl_sifra in existing_artikli:
                    stavka.artikal_id = existing_artikli[stavka.artikl_sifra].id
                    linked += 1
            
            await session.commit()
            
            logger.info("backfill.linked_stavke", count=linked)
            print(f"   Linked {linked} stavke to catalog articles")
            
    finally:
        await engine.dispose()
    
    logger.info("backfill.done")
    print("\n🎉 Backfill complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("backfill.interrupted")
        print("\n⚠️  Backfill interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.error("backfill.failed", error=str(exc), exc_info=True)
        print(f"\n❌ Backfill failed: {exc}")
        sys.exit(1)
