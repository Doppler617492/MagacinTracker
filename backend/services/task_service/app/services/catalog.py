from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Iterable, Optional

from prometheus_client import Counter, Gauge, Histogram
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app_common.logging import get_logger

from ..models import Artikal, ArtikalBarkod, CatalogSyncStatus
from ..models.enums import AuditAction
from ..schemas.catalog import (
    CatalogArticleResponse,
    CatalogArticleUpdate,
    CatalogBarcode,
    CatalogLookupResponse,
    CatalogUpsertItem,
    CatalogUpsertRequest,
    CatalogUpsertResponse,
)
from ..services.audit import record_audit

logger = get_logger(__name__)

SYNC_DURATION = Histogram("catalog_sync_duration_ms", "Catalog sync duration in milliseconds")
UPSERT_COUNTER = Counter(
    "catalog_upsert_items_total",
    "Catalog upsert item counts",
    labelnames=("state",),
)
LAST_SUCCESS_GAUGE = Gauge("catalog_sync_last_success_ts", "Last successful catalog sync timestamp")


class CatalogService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def upsert_batch(
        self,
        request: CatalogUpsertRequest,
        *,
        executed_by: Optional[uuid.UUID],
    ) -> tuple[CatalogUpsertResponse, bool]:
        start = time.perf_counter()
        payload_hash = request.options.payload_hash

        if payload_hash:
            cached = await self._check_idempotency(payload_hash)
            if cached:
                response = CatalogUpsertResponse(
                    processed=cached.processed,
                    created=cached.created,
                    updated=cached.updated,
                    deactivated=cached.deactivated,
                    duration_ms=float(cached.duration_ms or 0.0),
                    cached=True,
                )
                return response, True

        existing = await self._load_existing([item.sifra for item in request.items])
        created = updated = 0
        seen_artikal_ids: set[uuid.UUID] = set()

        for item in request.items:
            artikal = existing.get(item.sifra)
            if artikal:
                changed = await self._update_artikal(artikal, item)
                seen_artikal_ids.add(artikal.id)
                if changed:
                    updated += 1
            else:
                artikal = await self._create_artikal(item)
                existing[item.sifra] = artikal
                seen_artikal_ids.add(artikal.id)
                created += 1

        deactivated = 0
        if request.options.deactivate_missing:
            deactivated = await self._deactivate_missing(seen_artikal_ids)

        await self.session.commit()

        duration_ms = (time.perf_counter() - start) * 1000
        SYNC_DURATION.observe(duration_ms)
        UPSERT_COUNTER.labels(state="created").inc(created)
        UPSERT_COUNTER.labels(state="updated").inc(updated)
        UPSERT_COUNTER.labels(state="deactivated").inc(deactivated)

        status = CatalogSyncStatus(
            id=uuid.uuid4(),
            payload_hash=payload_hash,
            source=request.options.source,
            executed_by_id=executed_by,
            processed=len(request.items),
            created=created,
            updated=updated,
            deactivated=deactivated,
            duration_ms=duration_ms,
            status="success",
            finished_at=datetime.now(timezone.utc),
        )
        self.session.add(status)

        await record_audit(
            self.session,
            action=AuditAction.catalog_sync,
            actor_id=executed_by,
            entity_type="catalog",
            entity_id=str(status.id),
            payload={
                "processed": status.processed,
                "created": status.created,
                "updated": status.updated,
                "deactivated": status.deactivated,
                "duration_ms": status.duration_ms,
                "source": status.source,
                "payload_hash": payload_hash,
            },
        )

        await self.session.commit()
        LAST_SUCCESS_GAUGE.set(status.finished_at.timestamp())

        response = CatalogUpsertResponse(
            processed=len(request.items),
            created=created,
            updated=updated,
            deactivated=deactivated,
            duration_ms=duration_ms,
            cached=False,
        )
        return response, False

    async def _check_idempotency(self, payload_hash: str) -> CatalogSyncStatus | None:
        stmt = (
            select(CatalogSyncStatus)
            .where(
                CatalogSyncStatus.payload_hash == payload_hash,
                CatalogSyncStatus.status == "success",
            )
            .order_by(CatalogSyncStatus.finished_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        status = result.scalar_one_or_none()
        return status

    async def _load_existing(self, sifre: Iterable[str]) -> dict[str, Artikal]:
        sifre_set = set(filter(None, sifre))
        if not sifre_set:
            return {}
        stmt = (
            select(Artikal)
            .options(joinedload(Artikal.barkodovi))
            .where(Artikal.sifra.in_(sifre_set))
        )
        rows = await self.session.execute(stmt)
        return {row.sifra: row for row in rows.scalars()}

    async def _deactivate_missing(self, active_ids: set[uuid.UUID]) -> int:
        stmt = select(Artikal).where(Artikal.aktivan.is_(True))
        if active_ids:
            stmt = stmt.where(~Artikal.id.in_(active_ids))
        rows = await self.session.execute(stmt)
        count = 0
        for artikal in rows.scalars():
            artikal.aktivan = False
            count += 1
        return count

    async def _create_artikal(self, item: CatalogUpsertItem) -> Artikal:
        artikal = Artikal(
            id=uuid.uuid4(),
            sifra=item.sifra,
            naziv=item.naziv or item.sifra,
            jedinica_mjere=item.jedinica_mjere or "kom",
            aktivan=item.aktivan,
        )
        self.session.add(artikal)
        await self.session.flush()
        await self._sync_barkodi(artikal, item.barkodovi)
        return artikal

    async def _update_artikal(self, artikal: Artikal, item: CatalogUpsertItem) -> bool:
        changed = False
        if item.naziv and item.naziv != artikal.naziv:
            artikal.naziv = item.naziv
            changed = True
        if item.jedinica_mjere and item.jedinica_mjere != artikal.jedinica_mjere:
            artikal.jedinica_mjere = item.jedinica_mjere
            changed = True
        if artikal.aktivan != item.aktivan:
            artikal.aktivan = item.aktivan
            changed = True
        barkod_changed = await self._sync_barkodi(artikal, item.barkodovi)
        return changed or barkod_changed

    async def _sync_barkodi(self, artikal: Artikal, barkodi: Iterable[CatalogBarcode]) -> bool:
        existing = {b.barkod: b for b in artikal.barkodovi}
        incoming = list(barkodi)
        changed = False

        desired_primary: str | None = None
        incoming_values = set()

        for idx, incoming_barkod in enumerate(incoming):
            incoming_values.add(incoming_barkod.value)
            is_primary = (
                incoming_barkod.is_primary if incoming_barkod.is_primary is not None else idx == 0
            )
            if is_primary and desired_primary is None:
                desired_primary = incoming_barkod.value

            if incoming_barkod.value in existing:
                barcode = existing[incoming_barkod.value]
                if barcode.is_primary != is_primary:
                    barcode.is_primary = is_primary
                    changed = True
            else:
                artikal.barkodovi.append(
                    ArtikalBarkod(
                        id=uuid.uuid4(),
                        artikal_id=artikal.id,
                        barkod=incoming_barkod.value,
                        is_primary=is_primary,
                    )
                )
                changed = True

        # ensure only values present in payload keep primary flag
        if not incoming_values:
            desired_primary = None

        if desired_primary is None and artikal.barkodovi:
            desired_primary = artikal.barkodovi[0].barkod

        for barcode in artikal.barkodovi:
            if incoming_values and barcode.barkod not in incoming_values:
                if barcode.is_primary:
                    barcode.is_primary = False
                    changed = True
                continue
            should_be_primary = desired_primary is not None and barcode.barkod == desired_primary
            if barcode.is_primary != should_be_primary:
                barcode.is_primary = should_be_primary
                changed = True

        return changed

    async def lookup(self, code: str) -> CatalogLookupResponse:
        """
        Lookup article by SKU (sifra) or barcode.
        
        Args:
            code: Either a SKU (sifra) or barcode value
            
        Returns:
            CatalogLookupResponse with article details or None values if not found
        """
        # Try to find by SKU first
        stmt = (
            select(Artikal)
            .options(joinedload(Artikal.barkodovi))
            .where(Artikal.sifra == code)
        )
        result = await self.session.execute(stmt)
        artikal = result.scalar_one_or_none()
        
        # If not found by SKU, try by barcode
        if not artikal:
            stmt = (
                select(Artikal)
                .join(ArtikalBarkod)
                .options(joinedload(Artikal.barkodovi))
                .where(ArtikalBarkod.barkod == code)
            )
            result = await self.session.execute(stmt)
            artikal = result.scalar_one_or_none()
        
        if not artikal:
            return CatalogLookupResponse(
                artikal_id=None,
                sifra=code,
                naziv=None,
                jedinica_mjere=None,
                aktivan=False,
                barkodovi=[],
            )

        return CatalogLookupResponse(
            artikal_id=artikal.id,
            sifra=artikal.sifra,
            naziv=artikal.naziv,
            jedinica_mjere=artikal.jedinica_mjere,
            aktivan=artikal.aktivan,
            barkodovi=[CatalogBarcode(value=b.barkod, is_primary=b.is_primary) for b in artikal.barkodovi],
        )

    async def list_articles(self, search: str | None, page: int, page_size: int) -> tuple[list[CatalogArticleResponse], int]:
        stmt = select(Artikal).options(joinedload(Artikal.barkodovi))
        if search:
            like = f"%{search}%"
            stmt = stmt.where(
                or_(
                    Artikal.sifra.ilike(like),
                    Artikal.naziv.ilike(like),
                    Artikal.id.in_(
                        select(ArtikalBarkod.artikal_id).where(ArtikalBarkod.barkod.ilike(like))
                    ),
                )
            )
        total = await self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        stmt = stmt.order_by(Artikal.sifra).limit(page_size).offset((page - 1) * page_size)
        rows = await self.session.execute(stmt)
        artikli = rows.unique().scalars().all()
        return [CatalogArticleResponse.from_model(a) for a in artikli], int(total or 0)

    async def update_article(self, artikal_id: uuid.UUID, payload: CatalogArticleUpdate, actor_id: Optional[uuid.UUID]) -> CatalogArticleResponse:
        artikal = await self.session.scalar(
            select(Artikal).options(joinedload(Artikal.barkodovi)).where(Artikal.id == artikal_id)
        )
        if not artikal:
            raise ValueError("Artikal not found")

        if payload.naziv is not None:
            artikal.naziv = payload.naziv
        if payload.jedinica_mjere is not None:
            artikal.jedinica_mjere = payload.jedinica_mjere
        if payload.aktivan is not None:
            artikal.aktivan = payload.aktivan

        if payload.barkodi is not None:
            await self._apply_manual_barkodi(artikal, payload.barkodi)

        await record_audit(
            self.session,
            action=AuditAction.catalog_manual_update,
            actor_id=actor_id,
            entity_type="catalog",
            entity_id=str(artikal.id),
            payload=payload.model_dump(exclude_none=True),
        )
        await self.session.commit()
        await self.session.refresh(artikal)
        return CatalogArticleResponse.from_model(artikal)

    async def _apply_manual_barkodi(self, artikal: Artikal, barkodi: Iterable[CatalogBarcode]) -> None:
        existing = {b.barkod: b for b in artikal.barkodovi}
        incoming = list(barkodi)
        desired_primary = None
        for b in incoming:
            if b.is_primary:
                desired_primary = b.value

        for value, barcode in list(existing.items()):
            if value not in {b.value for b in incoming}:
                self.session.delete(barcode)

        for idx, item in enumerate(incoming):
            is_primary = item.is_primary if item.is_primary is not None else idx == 0
            if item.value in existing:
                existing[item.value].is_primary = is_primary
            else:
                artikal.barkodovi.append(
                    ArtikalBarkod(
                        id=uuid.uuid4(),
                        artikal_id=artikal.id,
                        barkod=item.value,
                        is_primary=is_primary,
                    )
                )

        primary_value = desired_primary
        if primary_value is None and artikal.barkodovi:
            primary_value = artikal.barkodovi[0].barkod
        if primary_value:
            for barcode in artikal.barkodovi:
                barcode.is_primary = barcode.barkod == primary_value

    async def get_last_status(self) -> CatalogSyncStatus | None:
        stmt = select(CatalogSyncStatus).order_by(CatalogSyncStatus.finished_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
