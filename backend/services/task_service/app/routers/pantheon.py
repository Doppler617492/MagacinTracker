"""
Pantheon Integration Backend Endpoints
Handles sync operations and data queries for Pantheon ERP integration
"""
from __future__ import annotations

import uuid
import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from app_common.logging import get_logger
from app_common.pantheon_client import PantheonAPIClient
from ..dependencies.auth import get_user_context
from ..models.location import Magacin, Radnja
from ..models.article import Artikal

logger = get_logger(__name__)
router = APIRouter()


# =========================================================================
# SYNC ENDPOINTS (Called by API Gateway)
# =========================================================================

@router.post("/pantheon/sync/catalog")
async def sync_catalog_endpoint(
    full_sync: bool = False,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """Trigger catalog sync from Pantheon"""
    try:
        from app_common.pantheon_client import PantheonAPIClient
        from ..models import Artikal, ArtikalBarkod
        
        logger.info(f"📊 Catalog sync triggered by user {user.id}")
        start_time = datetime.utcnow()
        
        stats = {
            "total_fetched": 0,
            "articles_created": 0,
            "articles_updated": 0,
            "barcodes_created": 0,
            "errors": 0
        }
        
        # Connect to Pantheon and fetch all articles with pagination
        async with PantheonAPIClient() as client:
            all_items = []
            offset = 0
            page_size = 1000  # Use larger page size for efficiency
            
            # Fetch all articles in batches
            while True:
                response = await client.get_ident_wms(limit=page_size, offset=offset)
                
                if not response or "items" not in response:
                    break
                    
                items = response.get("items", [])
                if not items:
                    break
                    
                all_items.extend(items)
                logger.info(f"Fetched {len(items)} articles (offset: {offset}, total so far: {len(all_items)})")
                
                # If we got fewer items than requested, we've reached the end
                if len(items) < page_size:
                    break
                    
                offset += page_size
                
                # Safety check to prevent infinite loops
                if offset > 50000:  # Max 50k articles
                    logger.warning("Reached maximum offset limit (50k), stopping pagination")
                    break
            
            if not all_items:
                return {
                    "status": "success",
                    "total_fetched": 0,
                    "articles_created": 0,
                    "articles_updated": 0,
                    "errors": 0,
                    "duration": 0,
                    "message": "No articles returned from Pantheon"
                }
            
            logger.info(f"Total articles fetched from Pantheon: {len(all_items)}")
            
            # Process each article
            for item in all_items:
                code = item.get("Ident") or item.get("sifra")
                
                # If no code, try to generate one or use a fallback
                if not code or code.strip() == "":
                    # Try to use name as fallback code, or generate UUID
                    naziv = item.get("Naziv") or item.get("naziv") or ""
                    if naziv and naziv.strip():
                        # Use first 20 chars of name as code
                        code = naziv.strip()[:20].replace(" ", "_").replace("/", "_")
                    else:
                        # Generate a unique code
                        import uuid
                        code = f"PANTHEON_{str(uuid.uuid4())[:8]}"
                
                # Ensure code is not empty
                if not code or code.strip() == "":
                    continue
                
                # Check if exists
                result = await session.execute(
                    select(Artikal).where(Artikal.sifra == code)
                )
                article = result.scalar_one_or_none()
                
                if article:
                    # Update
                    article.naziv = item.get("Naziv") or item.get("naziv") or ""
                    article.jedinica_mjere = item.get("JM") or item.get("jedinica_mjere") or "kom"
                    article.supplier = item.get("Dobavljac")
                    article.aktivan = item.get("Aktivan", "T") == "T"
                    article.last_synced_at = datetime.utcnow()
                    stats["articles_updated"] += 1
                else:
                    # Create
                    article = Artikal(
                        sifra=code,
                        naziv=item.get("Naziv") or item.get("naziv") or "",
                        jedinica_mjere=item.get("JM") or "kom",
                        supplier=item.get("Dobavljac"),
                        aktivan=item.get("Aktivan", "T") == "T",
                        last_synced_at=datetime.utcnow(),
                        source="PANTHEON"
                    )
                    session.add(article)
                    await session.flush()
                    stats["articles_created"] += 1
                    
                    # Handle barcodes
                    barcodes_data = item.get("Barkodovi", [])
                    for barcode_obj in barcodes_data:
                        barcode_value = barcode_obj.get("Barkod") if isinstance(barcode_obj, dict) else barcode_obj
                        if barcode_value:
                            barcode = ArtikalBarkod(
                                artikal_id=article.id,
                                barkod=barcode_value,
                                is_primary=True
                            )
                            session.add(barcode)
                            stats["barcodes_created"] += 1
                
                stats["total_fetched"] += 1
            
            await session.commit()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Catalog sync completed: {stats['articles_created']} created, {stats['articles_updated']} updated")
        
        return {
            "status": "success",
            "total_fetched": stats["total_fetched"],
            "articles_created": stats["articles_created"],
            "articles_updated": stats["articles_updated"],
            "barcodes_created": stats["barcodes_created"],
            "errors": stats["errors"],
            "duration": duration
        }
    except Exception as e:
        logger.error(f"Catalog sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pantheon/sync/subjects")
async def sync_subjects_endpoint(
    full_sync: bool = False,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """Trigger subjects sync from Pantheon"""
    try:
        from app_common.pantheon_client import PantheonAPIClient
        from ..models import Subject
        from ..models.enums import SubjectType
        
        logger.info(f"👥 Subjects sync triggered by user {user.id}")
        start_time = datetime.utcnow()
        
        stats = {
            "total_fetched": 0,
            "subjects_created": 0,
            "subjects_updated": 0,
            "by_type": {"supplier": 0, "customer": 0, "warehouse": 0},
            "errors": 0
        }
        
        # Connect to Pantheon and fetch subjects
        async with PantheonAPIClient() as client:
            response = await client.get_subject_wms(limit=100, offset=0)
            
            if not response or "items" not in response:
                return {
                    "status": "success",
                    "total_fetched": 0,
                    "subjects_created": 0,
                    "subjects_updated": 0,
                    "by_type": stats["by_type"],
                    "errors": 0,
                    "duration": 0,
                    "message": "No subjects returned from Pantheon"
                }
            
            items = response.get("items", [])
            logger.info(f"Received {len(items)} subjects from Pantheon")
            
            # Process each subject (simplified - just store what we get)
            for item in items:
                code = item.get("Sifra") or item.get("sifra") or item.get("code")
                
                # If no code, try to generate one or use a fallback
                if not code or code.strip() == "":
                    # Try to use name as fallback code, or generate UUID
                    naziv = item.get("Naziv") or item.get("naziv") or ""
                    if naziv and naziv.strip():
                        # Use first 20 chars of name as code
                        code = naziv.strip()[:20].replace(" ", "_").replace("/", "_")
                    else:
                        # Generate a unique code
                        import uuid
                        code = f"SUBJECT_{str(uuid.uuid4())[:8]}"
                
                # Ensure code is not empty
                if not code or code.strip() == "":
                    continue
                
                # Check if exists
                result = await session.execute(
                    select(Subject).where(Subject.code == code)
                )
                subject = result.scalar_one_or_none()
                
                # Classify type (simple heuristic)
                subject_type = SubjectType.SUPPLIER  # Default
                
                if subject:
                    # Update
                    subject.name = item.get("Naziv") or item.get("naziv") or ""
                    subject.last_synced_at = datetime.utcnow()
                    stats["subjects_updated"] += 1
                else:
                    # Create
                    subject = Subject(
                        code=code,
                        name=item.get("Naziv") or item.get("naziv") or "",
                        type=subject_type,
                        aktivan=True,
                        last_synced_at=datetime.utcnow(),
                        source="PANTHEON"
                    )
                    session.add(subject)
                    stats["subjects_created"] += 1
                
                stats["total_fetched"] += 1
                stats["by_type"]["supplier"] += 1
            
            await session.commit()
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        logger.info(f"✅ Subjects sync completed: {stats['subjects_created']} created, {stats['subjects_updated']} updated")
        
        return {
            "status": "success",
            "total_fetched": stats["total_fetched"],
            "subjects_created": stats["subjects_created"],
            "subjects_updated": stats["subjects_updated"],
            "by_type": stats["by_type"],
            "errors": stats["errors"],
            "duration": duration
        }
    except Exception as e:
        logger.error(f"Subjects sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pantheon/sync/dispatches")
async def sync_dispatches_endpoint(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """
    🔄 Automatski import trebovanja iz Pantheon-a
    
    ✅ READ-ONLY (samo čitanje, ništa ne piše na Pantheon)
    ✅ Rate limiting (1 poziv/sekunda)
    ✅ Delta sync (samo nova trebovanja od juče)
    ✅ Circuit breaker (zaštita servera)
    """
    try:
        start_time = datetime.utcnow()
        logger.info(f"📤 Pantheon → WMS: Pokretanje sinhronizacije trebovanja (READ-ONLY)")
        logger.info(f"📤 Pokrenut od korisnika: {user.id}")
        
        # Postavi datum range (od juče pa nadalje ako nije specificirano)
        if not date_from:
            date_from_obj = date.today() - timedelta(days=1)  # Od juče
            logger.info(f"📅 Uzimam trebovanja od JUČE ({date_from_obj})")
        else:
            date_from_obj = date.fromisoformat(date_from)
            
        date_to_obj = date.fromisoformat(date_to) if date_to else date.today()
        
        stats = {
            "trebovanja_created": 0,
            "trebovanja_updated": 0,
            "stavke_created": 0,
            "stavke_skipped": 0,  # Artikli koji ne postoje u WMS
            "errors": 0
        }
        
        # Inicijalizuj Pantheon klijent (READ-ONLY!) sa async context manager
        async with PantheonAPIClient() as client:
            await client.authenticate()
            
            # Pozovi GetIssueDocWMS (READ-ONLY metoda!)
            logger.info(f"📖 READ: GetIssueDocWMS od {date_from_obj} do {date_to_obj}")
            response = await client.get_issue_doc_wms(
                date_from=str(date_from_obj),
                date_to=str(date_to_obj),
                limit=1000  # Max 1000 dokumenata po pozivu
            )
            
            if not response:
                logger.error("❌ Pantheon nije vratio podatke!")
                return {
                    "status": "error",
                    "message": "Pantheon nije vratio podatke",
                    "trebovanja_created": 0,
                    "trebovanja_updated": 0,
                    "stavke_created": 0,
                    "duration_seconds": 0
                }
        
        items = response.get("items", [])
        logger.info(f"📥 Primljeno {len(items)} dokumenata iz Pantheon-a")
        
        if len(items) == 0:
            logger.info("⏸️ Nema novih trebovanja - preskaćem sync")
            return {
                "status": "success",
                "message": "Nema novih trebovanja",
                "trebovanja_created": 0,
                "trebovanja_updated": 0,
                "stavke_created": 0,
                "duration_seconds": 0
            }
        
        # Procesiraj svaki dokument
        from ..models.trebovanje import Trebovanje, TrebovanjeStavka, TrebovanjeStatus
        
        for doc in items:
            try:
                # Pantheon API vraća "BrojDokumenta", ne "DocNo"!
                doc_no = doc.get("BrojDokumenta") or ""
                if not doc_no:
                    logger.warning("⚠️ Dokument bez broja - preskačem")
                    continue
                
                # Proveri da li trebovanje već postoji
                result = await session.execute(
                    select(Trebovanje).where(Trebovanje.dokument_broj == doc_no)
                )
                postojece = result.scalar_one_or_none()
                
                if postojece:
                    logger.info(f"⏭️ Trebovanje {doc_no} već postoji - preskačem")
                    stats["trebovanja_updated"] += 1
                    continue
                
                # Uzmi prvi magacin i prvu radnju (potrebni za model)
                # TODO: Mapirati Pantheon warehouse → WMS magacin/radnja
                magacin_result = await session.execute(select(Magacin).limit(1))
                magacin = magacin_result.scalar_one_or_none()
                radnja_result = await session.execute(select(Radnja).limit(1))
                radnja = radnja_result.scalar_one_or_none()
                
                if not magacin or not radnja:
                    logger.error("❌ Nema magacina ili radnje u sistemu!")
                    stats["errors"] += 1
                    continue
                
                # Kreiraj novo trebovanje
                # Pantheon vraća: BrojDokumenta, TipDokumenta, DatumDokumenta, NasObjekat, Primalac1, Primalac2, OdgovornaOsoba, StatusDokumenta, Napomena, Objekti
                novo_trebovanje = Trebovanje(
                    dokument_broj=doc_no,
                    datum=datetime.now(timezone.utc),
                    magacin_id=magacin.id,
                    radnja_id=radnja.id,
                    status=TrebovanjeStatus.new,
                    meta={
                        "source": "PANTHEON",
                        "TipDokumenta": doc.get('TipDokumenta', ''),
                        "DatumDokumenta": doc.get('DatumDokumenta', ''),
                        "NasObjekat": doc.get('NasObjekat', ''),
                        "Primalac1": doc.get('Primalac1', ''),
                        "Primalac2": doc.get('Primalac2', ''),
                        "OdgovornaOsoba": doc.get('OdgovornaOsoba', ''),
                        "StatusDokumenta": doc.get('StatusDokumenta', ''),
                        "Napomena": doc.get('Napomena', '')
                    }
                )
                session.add(novo_trebovanje)
                await session.flush()  # Da dobijemo ID
                
                # Procesiraj stavke trebovanja
                # Pantheon vraća "Objekti", ne "Items"!
                stavke = doc.get("Objekti", [])
                for stavka_data in stavke:
                    # Pantheon vraća "Ident", ne "ArticleCode"!
                    article_code = stavka_data.get("Ident") or ""
                    if not article_code:
                        continue
                    
                    # Proveri da li artikal postoji u WMS katalogu
                    artikal_result = await session.execute(
                        select(Artikal).where(Artikal.sifra == article_code)
                    )
                    artikal = artikal_result.scalar_one_or_none()
                    
                    if not artikal:
                        logger.warning(f"⚠️ Artikal {article_code} ne postoji u WMS katalogu - preskačem")
                        stats["stavke_skipped"] += 1
                        continue
                    
                    # Kreiraj stavku trebovanja
                    # Pantheon vraća "Kolicina", ne "Quantity"!
                    kolicina = float(stavka_data.get("Kolicina", 0) or 0)
                    
                    if kolicina <= 0:
                        logger.warning(f"⚠️ Artikal {article_code} ima količinu 0 ili negativnu - preskačem")
                        stats["stavke_skipped"] += 1
                        continue
                    
                    stavka = TrebovanjeStavka(
                        trebovanje_id=novo_trebovanje.id,
                        artikal_id=artikal.id,
                        artikl_sifra=artikal.sifra,
                        naziv=artikal.naziv,
                        kolicina_trazena=kolicina,
                        kolicina_uradjena=0,
                        picked_qty=0,
                        missing_qty=0,
                        status=TrebovanjeItemStatus.new
                    )
                    session.add(stavka)
                    stats["stavke_created"] += 1
                
                await session.commit()
                stats["trebovanja_created"] += 1
                logger.info(f"✅ Kreirano trebovanje {doc_no} sa {stats['stavke_created']} stavki")
                
                # Rate limiting - čekaj 1 sekundu između dokumenata
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Greška kod dokumenta {doc.get('DocNo', 'unknown')}: {e}")
                stats["errors"] += 1
                await session.rollback()
                continue
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info(f"✅ Pantheon sync završen: {stats['trebovanja_created']} novih trebovanja u {duration:.2f}s")
        
        return {
            "status": "success",
            "message": f"Kreirano {stats['trebovanja_created']} novih trebovanja iz Pantheon-a",
            "total_fetched": len(items),
            "trebovanja_created": stats["trebovanja_created"],
            "trebovanja_updated": stats["trebovanja_updated"],
            "stavke_created": stats["stavke_created"],
            "stavke_skipped": stats["stavke_skipped"],
            "errors": stats["errors"],
            "duration_seconds": duration
        }
        
    except Exception as e:
        logger.error(f"❌ Pantheon sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pantheon/sync/receipts")
async def sync_receipts_endpoint(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """Trigger receipts sync from Pantheon"""
    try:
        # Implement receipt sync directly (no cross-service import)
        logger.info("📥 Implementing receipt sync directly in task service")
        
        logger.info(f"📥 Receipt sync triggered by user {user.id}")
        
        date_from_obj = date.fromisoformat(date_from) if date_from else None
        date_to_obj = date.fromisoformat(date_to) if date_to else None
        
        # Simple implementation for now - just return success
        return {
            "status": "success",
            "message": "Receipt sync endpoint ready - implementation in progress",
            "total_docs": 0,
            "docs_created": 0,
            "docs_updated": 0,
            "total_items": 0,
            "errors": 0,
            "duration": 0
        }
    except Exception as e:
        logger.error(f"Receipt sync failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# DATA QUERY ENDPOINTS
# =========================================================================

@router.get("/pantheon/catalog")
async def get_catalog_data(
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db)
):
    """Get catalog data for catalog service sync"""
    try:
        from ..models import Artikal, ArtikalBarkod
        from ..schemas.catalog import CatalogUpsertItem, CatalogBarcode
        
        # Build query with barcodes
        query = select(Artikal).where(Artikal.aktivan == True)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit).order_by(Artikal.sifra)
        result = await session.execute(query)
        articles = result.scalars().all()
        
        # Convert to catalog format
        catalog_items = []
        for article in articles:
            # Get barcodes for this article
            barcodes_query = select(ArtikalBarkod).where(ArtikalBarkod.artikal_id == article.id)
            barcodes_result = await session.execute(barcodes_query)
            barcodes = barcodes_result.scalars().all()
            
            catalog_barcodes = [
                CatalogBarcode(
                    value=barcode.barkod,
                    is_primary=barcode.is_primary
                )
                for barcode in barcodes
            ]
            
            catalog_item = CatalogUpsertItem(
                sifra=article.sifra,
                naziv=article.naziv,
                jedinica_mjere=article.jedinica_mjere,
                barkodovi=catalog_barcodes,
                aktivan=article.aktivan
            )
            catalog_items.append(catalog_item)
        
        return {
            "items": [item.model_dump() for item in catalog_items],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to get catalog data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/pantheon/subjects")
async def list_subjects(
    type: Optional[str] = Query(None, description="Filter by type: supplier, customer, warehouse"),
    aktivan: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """List subjects/partners from Pantheon"""
    try:
        from ..models import Subject
        
        # Build query
        query = select(Subject)
        
        if type:
            query = query.where(Subject.type == type)
        
        if aktivan is not None:
            query = query.where(Subject.aktivan == aktivan)
        
        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination
        query = query.offset(offset).limit(limit).order_by(Subject.name)
        
        result = await session.execute(query)
        subjects = result.scalars().all()
        
        return {
            "items": [
                {
                    "id": str(s.id),
                    "code": s.code,
                    "name": s.name,
                    "type": s.type.value if hasattr(s.type, 'value') else s.type,
                    "pib": s.pib,
                    "address": s.address,
                    "city": s.city,
                    "postal_code": s.postal_code,
                    "country": s.country,
                    "phone": s.phone,
                    "email": s.email,
                    "aktivan": s.aktivan,
                    "last_synced_at": s.last_synced_at.isoformat() if s.last_synced_at else None,
                    "source": s.source
                }
                for s in subjects
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Failed to list subjects: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pantheon/dispatches")
async def list_dispatches(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    doc_type: Optional[str] = Query(None),
    only_wms: bool = Query(False),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """List dispatch documents"""
    try:
        from ..models import Dispatch, DispatchItem, DocType
        
        # Build query
        query = select(Dispatch).join(Dispatch.doc_type)
        
        if date_from:
            query = query.where(Dispatch.date >= date_from)
        if date_to:
            query = query.where(Dispatch.date <= date_to)
        if doc_type:
            query = query.join(DocType).where(DocType.code == doc_type)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Paginate
        query = query.offset(offset).limit(limit).order_by(Dispatch.date.desc())
        result = await session.execute(query)
        dispatches = result.scalars().all()
        
        # Load items
        items_list = []
        for dispatch in dispatches:
            items_query = select(DispatchItem).where(DispatchItem.dispatch_id == dispatch.id)
            
            if only_wms:
                items_query = items_query.where(DispatchItem.exists_in_wms == True)
            
            items_result = await session.execute(items_query)
            items = items_result.scalars().all()
            
            items_list.append({
                "id": str(dispatch.id),
                "doc_no": dispatch.doc_no,
                "date": dispatch.date.isoformat(),
                "items_total": len(items),
                "items_wms": sum(1 for i in items if i.exists_in_wms),
                "items": [
                    {
                        "id": str(item.id),
                        "code": item.code,
                        "name": item.name,
                        "unit": item.unit,
                        "qty_requested": float(item.qty_requested),
                        "qty_completed": float(item.qty_completed),
                        "exists_in_wms": item.exists_in_wms,
                        "status": item.status.value if hasattr(item.status, 'value') else item.status
                    }
                    for item in items
                ]
            })
        
        return {
            "items": items_list,
            "total": total
        }
        
    except Exception as e:
        logger.error(f"Failed to list dispatches: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pantheon/receipts")
async def list_receipts(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_db),
    user: dict = Depends(get_user_context)
):
    """List receipt documents"""
    try:
        from ..models import Receipt
        
        query = select(Receipt)
        
        if date_from:
            query = query.where(Receipt.date >= date_from)
        if date_to:
            query = query.where(Receipt.date <= date_to)
        
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        query = query.offset(offset).limit(limit).order_by(Receipt.date.desc())
        result = await session.execute(query)
        receipts = result.scalars().all()
        
        return {
            "items": [
                {
                    "id": str(r.id),
                    "doc_no": r.doc_no,
                    "date": r.date.isoformat(),
                    "last_synced_at": r.last_synced_at.isoformat() if r.last_synced_at else None
                }
                for r in receipts
            ],
            "total": total
        }
    except Exception as e:
        logger.error(f"Failed to list receipts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

