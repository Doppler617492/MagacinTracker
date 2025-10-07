from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app_common.events import publish

from ..models import (
    ManualOverride,
    ScanLog,
    Trebovanje,
    TrebovanjeStavka,
    UserAccount,
    UserRole,
    Zaduznica,
    ZaduznicaStavka,
)
from ..models.enums import (
    AuditAction,
    Role,
    ScanResult,
    TrebovanjeItemStatus,
    TrebovanjeStatus,
    ZaduznicaItemStatus,
    ZaduznicaStatus,
)
from ..schemas import (
    ManualCompleteRequest,
    ScanRequest,
    WorkerTask,
    WorkerTaskDetail,
    WorkerTaskItem,
    ZaduznicaCreateRequest,
    ZaduznicaDetail,
    ZaduznicaItemDetail,
)
from .audit import record_audit

TV_CHANNEL = "tv:delta"


def _to_decimal(value: float | Decimal | int) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


async def _validate_magacioner(session: AsyncSession, user_id: UUID) -> None:
    result = await session.execute(
        select(UserAccount.id)
        .join(UserRole, UserRole.user_id == UserAccount.id)
        .where(UserAccount.id == user_id, UserRole.role == Role.magacioner)
    )
    if result.scalar_one_or_none() is None:
        raise ValueError("Magacioner not found or missing role")


async def _load_trebovanje(session: AsyncSession, trebovanje_id: UUID) -> Trebovanje:
    trebovanje = await session.scalar(
        select(Trebovanje)
        .options(joinedload(Trebovanje.stavke))
        .where(Trebovanje.id == trebovanje_id)
    )
    if not trebovanje:
        raise ValueError("Trebovanje not found")
    return trebovanje


async def _current_allocations(session: AsyncSession, trebovanje_id: UUID) -> dict[UUID, Decimal]:
    rows = await session.execute(
        select(
            ZaduznicaStavka.trebovanje_stavka_id,
            func.coalesce(func.sum(ZaduznicaStavka.trazena_kolicina), 0),
        )
        .join(Zaduznica, Zaduznica.id == ZaduznicaStavka.zaduznica_id)
        .where(Zaduznica.trebovanje_id == trebovanje_id)
        .group_by(ZaduznicaStavka.trebovanje_stavka_id)
    )
    return {row[0]: Decimal(row[1]) for row in rows}


async def create_zaduznice(
    session: AsyncSession,
    payload: ZaduznicaCreateRequest,
    *,
    actor_id: UUID | None,
) -> list[UUID]:
    trebovanje = await _load_trebovanje(session, payload.trebovanje_id)

    if trebovanje.status not in {TrebovanjeStatus.new, TrebovanjeStatus.assigned, TrebovanjeStatus.in_progress}:
        raise ValueError("Trebovanje nije u stanju za dodjelu")

    stavke_map = {stavka.id: stavka for stavka in trebovanje.stavke}
    allocations = await _current_allocations(session, trebovanje.id)

    created_ids: list[UUID] = []

    for assignment in payload.assignments:
        if not assignment.items:
            raise ValueError("Dodjela mora imati stavke")
        await _validate_magacioner(session, assignment.magacioner_id)

        zaduznica_id = uuid.uuid4()
        zaduznica = Zaduznica(
            id=zaduznica_id,
            trebovanje_id=trebovanje.id,
            magacioner_id=assignment.magacioner_id,
            prioritet=assignment.priority,
            rok=assignment.due_at,
            status=ZaduznicaStatus.assigned,
        )
        session.add(zaduznica)
        await session.flush()

        for item in assignment.items:
            target = stavke_map.get(item.trebovanje_stavka_id)
            if not target:
                raise ValueError("Nepostojeća stavka trebovanja")

            already = allocations.get(target.id, Decimal("0"))
            new_total = already + _to_decimal(item.quantity)
            if new_total > _to_decimal(target.kolicina_trazena):
                raise ValueError("Dodjela prelazi traženu količinu")

            allocations[target.id] = new_total

            session.add(
                ZaduznicaStavka(
                    id=uuid.uuid4(),
                    zaduznica_id=zaduznica_id,
                    trebovanje_stavka_id=target.id,
                    trazena_kolicina=_to_decimal(item.quantity),
                )
            )
            target.status = TrebovanjeItemStatus.assigned

        created_ids.append(zaduznica_id)
        await record_audit(
            session,
            action=AuditAction.zaduznica_assigned,
            actor_id=actor_id,
            entity_type="zaduznica",
            entity_id=str(zaduznica_id),
            payload={
                "trebovanje_id": str(trebovanje.id),
                "magacioner_id": str(assignment.magacioner_id),
            },
        )

    trebovanje.status = TrebovanjeStatus.assigned
    await session.commit()
    await publish(
        TV_CHANNEL,
        {"type": "assign", "trebovanje_id": str(trebovanje.id), "zaduznice": [str(z) for z in created_ids]},
    )
    return created_ids


async def update_zaduznica_status(
    session: AsyncSession,
    zaduznica_id: UUID,
    status: ZaduznicaStatus,
    *,
    actor_id: UUID | None,
) -> None:
    zaduznica = await session.scalar(select(Zaduznica).where(Zaduznica.id == zaduznica_id))
    if not zaduznica:
        raise ValueError("Zadužnica ne postoji")

    zaduznica.status = status
    zaduznica.updated_at = datetime.now(timezone.utc)

    await record_audit(
        session,
        action=AuditAction.zaduznica_assigned,
        actor_id=actor_id,
        entity_type="zaduznica",
        entity_id=str(zaduznica_id),
        payload={"status": status.value},
    )

    await session.commit()
    await publish(TV_CHANNEL, {"type": "status", "zaduznica_id": str(zaduznica_id), "status": status.value})


async def reassign_zaduznica(
    session: AsyncSession,
    zaduznica_id: UUID,
    target_magacioner_id: UUID,
    *,
    actor_id: UUID | None,
) -> None:
    await _validate_magacioner(session, target_magacioner_id)

    zaduznica = await session.scalar(select(Zaduznica).where(Zaduznica.id == zaduznica_id))
    if not zaduznica:
        raise ValueError("Zadužnica ne postoji")

    zaduznica.magacioner_id = target_magacioner_id
    zaduznica.status = ZaduznicaStatus.assigned
    zaduznica.updated_at = datetime.now(timezone.utc)

    await record_audit(
        session,
        action=AuditAction.zaduznica_reassigned,
        actor_id=actor_id,
        entity_type="zaduznica",
        entity_id=str(zaduznica_id),
        payload={"magacioner_id": str(target_magacioner_id)},
    )

    await session.commit()
    await publish(
        TV_CHANNEL,
        {
            "type": "reassign",
            "zaduznica_id": str(zaduznica_id),
            "magacioner_id": str(target_magacioner_id),
        },
    )


async def _sum_obradjena(session: AsyncSession, trebovanje_stavka_id: UUID) -> Decimal:
    result = await session.execute(
        select(func.coalesce(func.sum(ZaduznicaStavka.obradjena_kolicina), 0)).where(
            ZaduznicaStavka.trebovanje_stavka_id == trebovanje_stavka_id
        )
    )
    return Decimal(result.scalar() or 0)


async def _refresh_parent_states(session: AsyncSession, zaduznica: Zaduznica) -> None:
    await session.refresh(zaduznica, attribute_names=["stavke"])
    if all(item.status == ZaduznicaItemStatus.done for item in zaduznica.stavke):
        zaduznica.status = ZaduznicaStatus.done
    elif any(item.status == ZaduznicaItemStatus.in_progress for item in zaduznica.stavke):
        zaduznica.status = ZaduznicaStatus.in_progress
    else:
        zaduznica.status = ZaduznicaStatus.assigned

    total_trazeno = sum(_to_decimal(item.trazena_kolicina) for item in zaduznica.stavke)
    total_obradjeno = sum(_to_decimal(item.obradjena_kolicina) for item in zaduznica.stavke)
    zaduznica.progress = float((total_obradjeno / total_trazeno * Decimal("100")) if total_trazeno else Decimal(0))

    trebovanje = await session.scalar(
        select(Trebovanje)
        .options(joinedload(Trebovanje.stavke))
        .where(Trebovanje.id == zaduznica.trebovanje_id)
    )
    if not trebovanje:
        return

    statuses = {stavka.status for stavka in trebovanje.stavke}
    if statuses == {TrebovanjeItemStatus.done}:
        trebovanje.status = TrebovanjeStatus.done
    elif TrebovanjeItemStatus.in_progress in statuses:
        trebovanje.status = TrebovanjeStatus.in_progress
    elif TrebovanjeItemStatus.assigned in statuses:
        trebovanje.status = TrebovanjeStatus.assigned
    else:
        trebovanje.status = TrebovanjeStatus.new

    trebovanje.updated_at = datetime.now(timezone.utc)


async def register_scan(
    session: AsyncSession,
    zaduznica_stavka_id: UUID,
    payload: ScanRequest,
    *,
    actor_id: UUID,
) -> None:
    zaduznica_stavka = await session.scalar(
        select(ZaduznicaStavka)
        .options(joinedload(ZaduznicaStavka.zaduznica))
        .where(ZaduznicaStavka.id == zaduznica_stavka_id)
    )
    if not zaduznica_stavka:
        raise ValueError("Stavka zadužnice ne postoji")

    zaduznica = zaduznica_stavka.zaduznica
    if not zaduznica:
        raise ValueError("Nedostaje parent zadužnica")

    increment = _to_decimal(payload.quantity)
    new_value = _to_decimal(zaduznica_stavka.obradjena_kolicina) + increment
    max_value = _to_decimal(zaduznica_stavka.trazena_kolicina)
    if new_value > max_value:
        new_value = max_value

    zaduznica_stavka.obradjena_kolicina = new_value
    if new_value >= max_value:
        zaduznica_stavka.status = ZaduznicaItemStatus.done
    else:
        zaduznica_stavka.status = ZaduznicaItemStatus.in_progress

    trebovanje_stavka = await session.get(TrebovanjeStavka, zaduznica_stavka.trebovanje_stavka_id)
    if trebovanje_stavka:
        total = await _sum_obradjena(session, trebovanje_stavka.id)
        trebovanje_stavka.kolicina_uradjena = total
        if total >= _to_decimal(trebovanje_stavka.kolicina_trazena):
            trebovanje_stavka.status = TrebovanjeItemStatus.done
        elif total > 0:
            trebovanje_stavka.status = TrebovanjeItemStatus.in_progress

    session.add(
        ScanLog(
            zaduznica_stavka_id=zaduznica_stavka_id,
            user_id=actor_id,
            barcode=payload.barcode,
            quantity=increment,
            result=ScanResult.match,
        )
    )

    await record_audit(
        session,
        action=AuditAction.scan_recorded,
        actor_id=actor_id,
        entity_type="zaduznica_stavka",
        entity_id=str(zaduznica_stavka_id),
        payload={"barcode": payload.barcode, "quantity": payload.quantity},
    )

    await _refresh_parent_states(session, zaduznica)
    await session.commit()
    await publish(
        TV_CHANNEL,
        {
            "type": "scan",
            "zaduznica_id": str(zaduznica.id),
            "zaduznica_stavka_id": str(zaduznica_stavka_id),
            "progress": zaduznica.progress,
        },
    )


async def manual_complete(
    session: AsyncSession,
    zaduznica_stavka_id: UUID,
    payload: ManualCompleteRequest,
    *,
    actor_id: UUID,
) -> None:
    await register_scan(
        session,
        zaduznica_stavka_id,
        ScanRequest(barcode="manual", quantity=payload.quantity),
        actor_id=actor_id,
    )

    session.add(
        ManualOverride(
            zaduznica_stavka_id=zaduznica_stavka_id,
            user_id=actor_id,
            reason=payload.reason,
        )
    )

    await record_audit(
        session,
        action=AuditAction.manual_complete,
        actor_id=actor_id,
        entity_type="zaduznica_stavka",
        entity_id=str(zaduznica_stavka_id),
        payload={"reason": payload.reason, "quantity": payload.quantity},
    )
    await session.commit()
    await publish(
        TV_CHANNEL,
        {"type": "manual", "zaduznica_stavka_id": str(zaduznica_stavka_id)},
    )


async def list_worker_tasks(session: AsyncSession, user_id: UUID) -> list[WorkerTask]:
    rows = await session.execute(
        select(Zaduznica)
        .options(
            joinedload(Zaduznica.stavke),
            joinedload(Zaduznica.trebovanje).joinedload(Trebovanje.radnja),
        )
        .where(Zaduznica.magacioner_id == user_id)
        .order_by(Zaduznica.created_at.desc())
    )

    tasks: list[WorkerTask] = []
    for zaduznica in rows.scalars().unique():
        total = sum(_to_decimal(item.trazena_kolicina) for item in zaduznica.stavke)
        done = sum(_to_decimal(item.obradjena_kolicina) for item in zaduznica.stavke)
        progress = float((done / total * Decimal("100")) if total else Decimal(0))
        dokument = (
            zaduznica.trebovanje.dokument_broj if zaduznica.trebovanje else str(zaduznica.trebovanje_id)
        )
        lokacija = (
            zaduznica.trebovanje.radnja.naziv
            if zaduznica.trebovanje and zaduznica.trebovanje.radnja
            else str(zaduznica.trebovanje_id)
        )
        tasks.append(
            WorkerTask(
                id=zaduznica.id,
                dokument=dokument,
                lokacija=lokacija,
                stavke_total=len(zaduznica.stavke),
                progress=progress,
                status=zaduznica.status,
                due_at=zaduznica.rok,
            )
        )
    return tasks


async def worker_task_detail(session: AsyncSession, zaduznica_id: UUID, user_id: UUID) -> WorkerTaskDetail:
    zaduznica = await session.scalar(
        select(Zaduznica)
        .options(
            joinedload(Zaduznica.stavke).joinedload(ZaduznicaStavka.trebovanje_stavka),
            joinedload(Zaduznica.trebovanje).joinedload(Trebovanje.radnja),
        )
        .where(Zaduznica.id == zaduznica_id, Zaduznica.magacioner_id == user_id)
    )
    if not zaduznica:
        raise ValueError("Zadužnica nije pronađena")

    items = [
        WorkerTaskItem(
            id=item.id,
            naziv=item.trebovanje_stavka.naziv if item.trebovanje_stavka else "",
            trazena_kolicina=float(item.trazena_kolicina),
            obradjena_kolicina=float(item.obradjena_kolicina),
            status=item.status.value,
            needs_barcode=item.trebovanje_stavka.needs_barcode if item.trebovanje_stavka else False,
        )
        for item in zaduznica.stavke
    ]

    total = sum(_to_decimal(item.trazena_kolicina) for item in zaduznica.stavke)
    done = sum(_to_decimal(item.obradjena_kolicina) for item in zaduznica.stavke)
    progress = float((done / total * Decimal("100")) if total else Decimal(0))

    dokument = (
        zaduznica.trebovanje.dokument_broj if zaduznica.trebovanje else str(zaduznica.trebovanje_id)
    )
    lokacija = (
        zaduznica.trebovanje.radnja.naziv
        if zaduznica.trebovanje and zaduznica.trebovanje.radnja
        else str(zaduznica.trebovanje_id)
    )

    return WorkerTaskDetail(
        id=zaduznica.id,
        dokument=dokument,
        lokacija=lokacija,
        stavke_total=len(items),
        progress=progress,
        status=zaduznica.status,
        due_at=zaduznica.rok,
        stavke=items,
    )


async def zaduznica_detail(session: AsyncSession, zaduznica_id: UUID) -> ZaduznicaDetail:
    zaduznica = await session.scalar(
        select(Zaduznica)
        .options(
            joinedload(Zaduznica.stavke).joinedload(ZaduznicaStavka.trebovanje_stavka),
            joinedload(Zaduznica.trebovanje).joinedload(Trebovanje.magacin),
            joinedload(Zaduznica.trebovanje).joinedload(Trebovanje.radnja),
        )
        .where(Zaduznica.id == zaduznica_id)
    )
    if not zaduznica:
        raise ValueError("Zadužnica nije pronađena")

    items = [
        ZaduznicaItemDetail(
            id=item.id,
            trebovanje_stavka_id=item.trebovanje_stavka_id,
            naziv=item.trebovanje_stavka.naziv if item.trebovanje_stavka else "",
            trazena_kolicina=float(item.trazena_kolicina),
            obradjena_kolicina=float(item.obradjena_kolicina),
            status=item.status,
        )
        for item in zaduznica.stavke
    ]

    total = sum(_to_decimal(item.trazena_kolicina) for item in zaduznica.stavke)
    done = sum(_to_decimal(item.obradjena_kolicina) for item in zaduznica.stavke)
    progress = float((done / total * Decimal("100")) if total else Decimal(0))

    return ZaduznicaDetail(
        id=zaduznica.id,
        dokument=zaduznica.trebovanje.dokument_broj if zaduznica.trebovanje else "",
        lokacija=zaduznica.trebovanje.magacin.naziv if zaduznica.trebovanje and zaduznica.trebovanje.magacin else "",
        radnja=zaduznica.trebovanje.radnja.naziv if zaduznica.trebovanje and zaduznica.trebovanje.radnja else "",
        status=zaduznica.status,
        prioritet=zaduznica.prioritet,
        due_at=zaduznica.rok,
        progress=progress,
        stavke=items,
    )
