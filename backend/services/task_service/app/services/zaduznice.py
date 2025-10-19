from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app_common.events import publish

from ..models import (
    ManualOverride,
    ScanLog,
    Team,
    Trebovanje,
    TrebovanjeStavka,
    UserAccount,
    Zaduznica,
    ZaduznicaStavka,
)
from ..models.enums import (
    AuditAction,
    DiscrepancyStatus,
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
        select(UserAccount.id).where(
            UserAccount.id == user_id,
            func.lower(cast(UserAccount.role, String)) == "magacioner",
            UserAccount.is_active.is_(True),
        )
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

    # Find team_id once for all assignments (if multiple assignments are for the same team)
    team_id_cache: dict[UUID, UUID | None] = {}
    
    for assignment in payload.assignments:
        if not assignment.items:
            raise ValueError("Dodjela mora imati stavke")
        await _validate_magacioner(session, assignment.magacioner_id)

        # Find team for this worker
        if assignment.magacioner_id not in team_id_cache:
            team_stmt = select(Team.id).where(
                ((Team.worker1_id == assignment.magacioner_id) | (Team.worker2_id == assignment.magacioner_id))
                & (Team.active == True)
            )
            team_result = await session.execute(team_stmt)
            team_id = team_result.scalar_one_or_none()
            team_id_cache[assignment.magacioner_id] = team_id
        else:
            team_id = team_id_cache[assignment.magacioner_id]

        zaduznica_id = uuid.uuid4()
        zaduznica = Zaduznica(
            id=zaduznica_id,
            trebovanje_id=trebovanje.id,
            magacioner_id=assignment.magacioner_id,
            team_id=team_id,  # Set team_id automatically
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


async def cancel_trebovanje_assignments(
    session: AsyncSession,
    trebovanje_id: UUID,
    *,
    actor_id: UUID | None,
) -> None:
    result = await session.execute(
        select(Zaduznica)
        .options(joinedload(Zaduznica.stavke))
        .where(Zaduznica.trebovanje_id == trebovanje_id)
    )
    zaduznice = list(result.scalars().unique())
    if not zaduznice:
        return

    for zaduznica in zaduznice:
        for stavka in zaduznica.stavke:
            if stavka.obradjena_kolicina and float(stavka.obradjena_kolicina) > 0:
                raise ValueError("Zadužnica je već u obradi i ne može se poništiti")

    trebovanje = await session.get(Trebovanje, trebovanje_id)
    if not trebovanje:
        raise ValueError("Trebovanje ne postoji")

    stavka_ids = {stavka.trebovanje_stavka_id for zaduznica in zaduznice for stavka in zaduznica.stavke}
    if stavka_ids:
        result = await session.execute(select(TrebovanjeStavka).where(TrebovanjeStavka.id.in_(stavka_ids)))
        for stavka in result.scalars():
            stavka.kolicina_uradjena = 0
            stavka.status = TrebovanjeItemStatus.new

    canceled_ids = [str(zaduznica.id) for zaduznica in zaduznice]
    for zaduznica in zaduznice:
        await record_audit(
            session,
            action=AuditAction.scheduler_override,
            actor_id=actor_id,
            entity_type="zaduznica",
            entity_id=str(zaduznica.id),
            payload={"action": "cancel"},
        )
        await session.delete(zaduznica)

    trebovanje.status = TrebovanjeStatus.new
    trebovanje.updated_at = datetime.utcnow()

    await session.commit()
    await publish(
        TV_CHANNEL,
        {"type": "cancel", "trebovanje_id": str(trebovanje_id), "zaduznice": canceled_ids},
    )


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
    
    # Publish TV update when trebovanje status changes
    await publish(
        TV_CHANNEL,
        {
            "type": "trebovanje_status_update",
            "trebovanje_id": str(trebovanje.id),
            "status": trebovanje.status.value,
            "progress": zaduznica.progress,
        },
    )


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
            joinedload(Zaduznica.trebovanje)
            .joinedload(Trebovanje.radnja),
            joinedload(Zaduznica.trebovanje)
            .joinedload(Trebovanje.magacin),
            joinedload(Zaduznica.trebovanje)
            .joinedload(Trebovanje.stavke),
        )
        .where(Zaduznica.magacioner_id == user_id)
        .order_by(Zaduznica.created_at.desc())
    )

    zaduznice = list(rows.scalars().unique())
    if not zaduznice:
        return []

    creator_ids = {
        zaduznica.trebovanje.created_by_id
        for zaduznica in zaduznice
        if zaduznica.trebovanje and zaduznica.trebovanje.created_by_id
    }

    assigned_users: dict[UUID, str] = {}
    if creator_ids:
        result = await session.execute(
            select(UserAccount.id, UserAccount.first_name, UserAccount.last_name).where(
                UserAccount.id.in_(creator_ids)
            )
        )
        assigned_users = {
            row[0]: f"{row[1]} {row[2]}".strip() for row in result.all()
        }

    tasks: list[WorkerTask] = []
    for zaduznica in zaduznice:
        trebovanje = zaduznica.trebovanje
        dokument = (
            trebovanje.dokument_broj if trebovanje else str(zaduznica.trebovanje_id)
        )
        lokacija = (
            trebovanje.radnja.naziv
            if trebovanje and trebovanje.radnja
            else str(zaduznica.trebovanje_id)
        )

        trebovanje_stavke_map = {}
        if trebovanje and trebovanje.stavke:
            trebovanje_stavke_map = {stavka.id: stavka for stavka in trebovanje.stavke}

        total_requested = Decimal("0")
        total_picked = Decimal("0")
        partial_items = 0
        shortage_qty = Decimal("0")
        completed_items = 0

        for item in zaduznica.stavke:
            total_requested += _to_decimal(item.trazena_kolicina)
            treb_stavka = trebovanje_stavke_map.get(item.trebovanje_stavka_id)
            if not treb_stavka:
                total_picked += _to_decimal(item.obradjena_kolicina)
                continue

            picked_qty = _to_decimal(treb_stavka.picked_qty)
            total_picked += picked_qty

            missing_qty = _to_decimal(treb_stavka.missing_qty)
            discrepancy_status = treb_stavka.discrepancy_status

            if (
                discrepancy_status
                and discrepancy_status != DiscrepancyStatus.none
                and missing_qty > 0
            ):
                partial_items += 1
                shortage_qty += missing_qty

            if picked_qty >= _to_decimal(item.trazena_kolicina) or (
                discrepancy_status and discrepancy_status != DiscrepancyStatus.none
            ):
                completed_items += 1

        progress = float(
            (total_picked / total_requested * Decimal("100"))
            if total_requested
            else Decimal(0)
        )

        tasks.append(
            WorkerTask(
                id=zaduznica.id,
                dokument=dokument,
                dokument_broj=dokument,
                lokacija=lokacija,
                lokacija_naziv=lokacija,
                stavke_total=len(zaduznica.stavke),
                stavke_completed=completed_items,
                partial_items=partial_items,
                shortage_qty=float(shortage_qty),
                assigned_by_id=trebovanje.created_by_id if trebovanje else None,
                assigned_by_name=assigned_users.get(
                    trebovanje.created_by_id
                )
                if trebovanje and trebovanje.created_by_id
                else None,
                progress=progress,
                status=zaduznica.status,
                due_at=zaduznica.rok,
                trebovanje_id=zaduznica.trebovanje_id,
            )
        )
    return tasks


async def worker_task_detail(session: AsyncSession, zaduznica_id: UUID, user_id: UUID) -> WorkerTaskDetail:
    zaduznica = await session.scalar(
        select(Zaduznica)
        .options(
            joinedload(Zaduznica.stavke),
            joinedload(Zaduznica.trebovanje)
            .joinedload(Trebovanje.radnja),
            joinedload(Zaduznica.trebovanje)
            .joinedload(Trebovanje.magacin),
            joinedload(Zaduznica.trebovanje)
            .joinedload(Trebovanje.stavke),
        )
        .where(Zaduznica.id == zaduznica_id, Zaduznica.magacioner_id == user_id)
    )
    if not zaduznica:
        raise ValueError("Zadužnica nije pronađena")

    # Get trebovanje stavke data for the items
    trebovanje_stavke_ids = [item.trebovanje_stavka_id for item in zaduznica.stavke]
    trebovanje_stavke = {}
    if trebovanje_stavke_ids:
        trebovanje_stavke_result = await session.execute(
            select(TrebovanjeStavka).where(TrebovanjeStavka.id.in_(trebovanje_stavke_ids))
        )
        for ts in trebovanje_stavke_result.scalars():
            trebovanje_stavke[ts.id] = ts

    items = []
    for item in zaduznica.stavke:
        trebovanje_stavka = trebovanje_stavke.get(item.trebovanje_stavka_id)
        if trebovanje_stavka:
            items.append(
                WorkerTaskItem(
                    id=trebovanje_stavka.id,
                    naziv=trebovanje_stavka.naziv,
                    artikl_sifra=trebovanje_stavka.artikl_sifra,
                    kolicina_trazena=float(item.trazena_kolicina),
                    picked_qty=float(trebovanje_stavka.picked_qty),
                    missing_qty=float(trebovanje_stavka.missing_qty),
                    discrepancy_status=trebovanje_stavka.discrepancy_status.value,
                    discrepancy_reason=trebovanje_stavka.discrepancy_reason,
                    needs_barcode=trebovanje_stavka.needs_barcode,
                    barkod=trebovanje_stavka.barkod,
                )
            )
        else:
            items.append(
                WorkerTaskItem(
                    id=item.id,
                    naziv="",
                    artikl_sifra="",
                    kolicina_trazena=float(item.trazena_kolicina),
                    picked_qty=float(item.obradjena_kolicina or 0),
                    missing_qty=float(item.trazena_kolicina),
                    discrepancy_status="none",
                    discrepancy_reason=None,
                    needs_barcode=False,
                    barkod=None,
                )
            )

    total = sum(_to_decimal(item.trazena_kolicina) for item in zaduznica.stavke)
    done = sum(_to_decimal(item.obradjena_kolicina) for item in zaduznica.stavke)
    progress = float((done / total * Decimal("100")) if total else Decimal(0))

    shortage_items = [
        item for item in items if item.discrepancy_status != DiscrepancyStatus.none.value and item.missing_qty > 0
    ]
    partial_count = len(shortage_items)
    shortage_qty = sum(item.missing_qty for item in shortage_items)
    
    # Calculate completed items based on trebovanje stavke status
    stavke_completed = sum(
        1 for item in zaduznica.stavke 
        if trebovanje_stavke.get(item.trebovanje_stavka_id) and 
           (float(trebovanje_stavke.get(item.trebovanje_stavka_id).picked_qty) >= float(item.trazena_kolicina) or 
            trebovanje_stavke.get(item.trebovanje_stavka_id).discrepancy_status.value != "none")
    )

    dokument = (
        zaduznica.trebovanje.dokument_broj if zaduznica.trebovanje else str(zaduznica.trebovanje_id)
    )
    lokacija = (
        zaduznica.trebovanje.radnja.naziv
        if zaduznica.trebovanje and zaduznica.trebovanje.radnja
        else str(zaduznica.trebovanje_id)
    )

    assigned_by_id = zaduznica.trebovanje.created_by_id if zaduznica.trebovanje else None
    assigned_by_name = None
    if assigned_by_id:
        assigned_user = await session.get(UserAccount, assigned_by_id)
        if assigned_user:
            assigned_by_name = assigned_user.full_name

    return WorkerTaskDetail(
        id=zaduznica.id,
        dokument=dokument,
        dokument_broj=dokument,
        lokacija=lokacija,
        lokacija_naziv=lokacija,
        stavke_total=len(items),
        stavke_completed=stavke_completed,
        partial_items=partial_count,
        shortage_qty=float(shortage_qty),
        assigned_by_id=assigned_by_id,
        assigned_by_name=assigned_by_name,
        progress=progress,
        status=zaduznica.status,
        due_at=zaduznica.rok,
        trebovanje_id=zaduznica.trebovanje_id,
        stavke=items,
    )


async def zaduznica_detail(session: AsyncSession, zaduznica_id: UUID) -> ZaduznicaDetail:
    zaduznica = await session.scalar(
        select(Zaduznica)
        .options(
            joinedload(Zaduznica.stavke),
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
