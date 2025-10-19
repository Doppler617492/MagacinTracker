from __future__ import annotations

import uuid
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from datetime import datetime, timezone

from ..models import (
    Artikal,
    ArtikalBarkod,
    ImportJob,
    Magacin,
    Radnja,
    Trebovanje,
    TrebovanjeStavka,
)
from ..models.enums import AuditAction, ImportStatus, TrebovanjeStatus
from ..services.audit import record_audit
from ..schemas import (
    TrebovanjeDetail,
    TrebovanjeImportPayload,
    TrebovanjeItemDetail,
    TrebovanjeListItem,
    TrebovanjeListResponse,
)


class TrebovanjeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    def _base_query(self) -> Select:
        return (
            select(
                Trebovanje,
                Magacin.naziv.label("magacin_naziv"),
                Radnja.naziv.label("radnja_naziv"),
                func.count(TrebovanjeStavka.id).label("broj_stavki"),
                func.coalesce(func.sum(TrebovanjeStavka.kolicina_trazena), 0).label("ukupno_trazena"),
                func.coalesce(func.sum(TrebovanjeStavka.kolicina_uradjena), 0).label("ukupno_uradjena"),
            )
            .join(Magacin, Magacin.id == Trebovanje.magacin_id)
            .join(Radnja, Radnja.id == Trebovanje.radnja_id)
            .outerjoin(Trebovanje.stavke)
            .group_by(Trebovanje.id, Magacin.naziv, Radnja.naziv)
        )

    async def list(
        self,
        page: int,
        page_size: int,
        status: TrebovanjeStatus | None = None,
        magacin_id: UUID | None = None,
        radnja_id: UUID | None = None,
        search: str | None = None,
    ) -> TrebovanjeListResponse:
        query = self._base_query()

        if status:
            query = query.where(Trebovanje.status == status)
        if magacin_id:
            query = query.where(Trebovanje.magacin_id == magacin_id)
        if radnja_id:
            query = query.where(Trebovanje.radnja_id == radnja_id)
        if search:
            like = f"%{search}%"
            query = query.where(Trebovanje.dokument_broj.ilike(like))

        total = await self.session.scalar(select(func.count()).select_from(query.subquery()))

        result = await self.session.execute(
            query.order_by(Trebovanje.created_at.desc())
            .limit(page_size)
            .offset((page - 1) * page_size)
        )

        items = [
            TrebovanjeListItem(
                id=row.Trebovanje.id,
                dokument_broj=row.Trebovanje.dokument_broj,
                datum=row.Trebovanje.datum,
                magacin=row.magacin_naziv,
                radnja=row.radnja_naziv,
                status=row.Trebovanje.status,
                broj_stavki=row.broj_stavki,
                ukupno_trazena=float(row.ukupno_trazena or 0),
                ukupno_uradjena=float(row.ukupno_uradjena or 0),
            )
            for row in result
        ]

        return TrebovanjeListResponse(
            page=page,
            page_size=page_size,
            total=int(total or 0),
            items=items,
        )

    async def get(self, trebovanje_id: UUID) -> TrebovanjeDetail:
        trebovanje = await self.session.scalar(
            select(Trebovanje)
            .options(joinedload(Trebovanje.magacin), joinedload(Trebovanje.radnja), joinedload(Trebovanje.stavke))
            .where(Trebovanje.id == trebovanje_id)
        )
        if not trebovanje:
            raise ValueError("Trebovanje not found")

        items = [
            TrebovanjeItemDetail(
                id=stavka.id,
                artikl_sifra=stavka.artikl_sifra,
                naziv=stavka.naziv,
                kolicina_trazena=float(stavka.kolicina_trazena),
                kolicina_uradjena=float(stavka.kolicina_uradjena),
                status=stavka.status.value,
            )
            for stavka in trebovanje.stavke
        ]

        return TrebovanjeDetail(
            id=trebovanje.id,
            dokument_broj=trebovanje.dokument_broj,
            datum=trebovanje.datum,
            status=trebovanje.status,
            magacin=trebovanje.magacin.naziv if trebovanje.magacin else "",
            radnja=trebovanje.radnja.naziv if trebovanje.radnja else "",
            broj_stavki=len(items),
            stavke=items,
        )

    async def delete(self, trebovanje_id: UUID, actor_id: UUID | None = None) -> None:
        """Delete a trebovanje and all its related data"""
        trebovanje = await self.session.get(Trebovanje, trebovanje_id)
        if not trebovanje:
            raise ValueError("Trebovanje not found")

        # Allow deletion of all trebovanja regardless of status
        # (Previously restricted in_progress and done, but user requested to allow deletion of finished documents)

        # Record audit before deletion
        await record_audit(
            self.session,
            action=AuditAction.trebovanje_deleted,
            actor_id=actor_id,
            entity_type="trebovanje",
            entity_id=str(trebovanje.id),
            payload={"dokument_broj": trebovanje.dokument_broj},
        )

        # Delete related import jobs first to avoid foreign key constraint violations
        from ..models import ImportJob
        import_jobs = await self.session.execute(
            select(ImportJob).where(ImportJob.trebovanje_id == trebovanje_id)
        )
        for import_job in import_jobs.scalars():
            await self.session.delete(import_job)

        # Delete the trebovanje (cascade will handle other related records)
        await self.session.delete(trebovanje)
        await self.session.commit()

    async def _ensure_magacin(self, pantheon_id: str, naziv: str | None) -> UUID:
        magacin = await self.session.scalar(select(Magacin).where(Magacin.pantheon_id == pantheon_id))
        if magacin:
            return magacin.id
        entity = Magacin(id=uuid.uuid4(), pantheon_id=pantheon_id, naziv=naziv or pantheon_id)
        self.session.add(entity)
        await self.session.flush()
        return entity.id

    async def _ensure_radnja(self, pantheon_id: str, naziv: str | None) -> UUID:
        radnja = await self.session.scalar(select(Radnja).where(Radnja.pantheon_id == pantheon_id))
        if radnja:
            return radnja.id
        entity = Radnja(id=uuid.uuid4(), pantheon_id=pantheon_id, naziv=naziv or pantheon_id)
        self.session.add(entity)
        await self.session.flush()
        return entity.id

    async def _ensure_artikal(self, sifra: str, naziv: str, barkod: str | None) -> UUID:
        artikal = await self.session.scalar(select(Artikal).where(Artikal.sifra == sifra))
        if not artikal:
            artikal = Artikal(id=uuid.uuid4(), sifra=sifra, naziv=naziv)
            self.session.add(artikal)
            await self.session.flush()
        elif artikal.naziv != naziv:
            artikal.naziv = naziv

        if barkod:
            existing_barcode = await self.session.scalar(
                select(ArtikalBarkod).where(ArtikalBarkod.barkod == barkod)
            )
            if not existing_barcode:
                self.session.add(
                    ArtikalBarkod(
                        id=uuid.uuid4(),
                        artikal_id=artikal.id,
                        barkod=barkod,
                        is_primary=True,
                    )
                )
        return artikal.id

    async def create_from_import(
        self,
        payload: TrebovanjeImportPayload,
        *,
        initiated_by: UUID | None,
    ) -> TrebovanjeDetail:
        existing = await self.session.scalar(
            select(Trebovanje).where(Trebovanje.dokument_broj == payload.dokument_broj)
        )
        if existing:
            raise ValueError("Dokument već postoji")

        magacin_id = await self._ensure_magacin(payload.magacin_pantheon_id, payload.magacin_naziv)
        radnja_id = await self._ensure_radnja(payload.radnja_pantheon_id, payload.radnja_naziv)

        now_utc = datetime.now(timezone.utc)
        meta = payload.meta or {}
        trebovanje = Trebovanje(
            id=uuid.uuid4(),
            dokument_broj=payload.dokument_broj,
            datum=payload.datum,
            magacin_id=magacin_id,
            radnja_id=radnja_id,
            status=TrebovanjeStatus.new,
            meta=meta,
            created_by_id=initiated_by,
            created_at=now_utc,
        )

        enriched_count = 0
        needs_barcode_count = 0

        for item in payload.stavke:
            artikal_id = item.artikl_id
            if not artikal_id:
                artikal_id = await self._ensure_artikal(item.artikl_sifra, item.naziv, item.barkod)

            needs_barcode = bool(item.needs_barcode)
            if needs_barcode:
                needs_barcode_count += 1
            else:
                enriched_count += 1

            trebovanje.stavke.append(
                TrebovanjeStavka(
                    id=uuid.uuid4(),
                    artikal_id=artikal_id,
                    artikl_sifra=item.artikl_sifra,
                    naziv=item.naziv,
                    kolicina_trazena=item.kolicina_trazena,
                    needs_barcode=needs_barcode,
                )
            )

        self.session.add(trebovanje)
        await self.session.flush()  # Ensure trebovanje gets an ID
        
        file_hash = meta.get("file_hash")
        import_job = ImportJob(
            id=uuid.uuid4(),
            file_name=meta.get("source_file", "manual"),
            file_hash=file_hash or str(uuid.uuid4()),
            status=ImportStatus.done,
            initiated_by_id=initiated_by,
            trebovanje_id=trebovanje.id,
            started_at=now_utc,
            finished_at=now_utc,
        )
        self.session.add(import_job)

        await record_audit(
            self.session,
            action=AuditAction.trebovanje_imported,
            actor_id=initiated_by,
            entity_type="trebovanje",
            entity_id=str(trebovanje.id),
            payload={"dokument_broj": trebovanje.dokument_broj},
        )

        await record_audit(
            self.session,
            action=AuditAction.catalog_enriched,
            actor_id=initiated_by,
            entity_type="trebovanje",
            entity_id=str(trebovanje.id),
            payload={
                "enriched": enriched_count,
                "needs_barcode": needs_barcode_count,
            },
        )

        await self.session.commit()
        return await self.get(trebovanje.id)
