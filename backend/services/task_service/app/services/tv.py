from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import (
    Radnja,
    ScanLog,
    Trebovanje,
    TrebovanjeStavka,
    UserAccount,
    Zaduznica,
    ZaduznicaStavka,
)
from ..models.enums import DiscrepancyStatus, ZaduznicaStatus
from ..schemas import KpiSnapshot, LeaderboardEntry, QueueEntry, TvSnapshot

SHIFT_END = time(hour=22, minute=0)


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


async def build_tv_snapshot(session: AsyncSession) -> TvSnapshot:
    now = datetime.now(timezone.utc)
    start_of_day = datetime.combine(now.date(), time.min, tzinfo=timezone.utc)

    leaderboard_stmt = (
        sa.select(
            UserAccount.id.label("user_id"),
            UserAccount.first_name.label("first_name"),
            UserAccount.last_name.label("last_name"),
            sa.func.coalesce(sa.func.sum(ScanLog.quantity), 0).label("qty"),
            sa.func.sum(sa.case((Zaduznica.status == ZaduznicaStatus.done, 1), else_=0)).label("tasks_done"),
            sa.func.count(Zaduznica.id).label("tasks_total"),
        )
        .select_from(Zaduznica)
        .join(UserAccount, UserAccount.id == Zaduznica.magacioner_id)
        .outerjoin(ZaduznicaStavka, ZaduznicaStavka.zaduznica_id == Zaduznica.id)
        .outerjoin(
            ScanLog,
            sa.and_(
                ScanLog.zaduznica_stavka_id == ZaduznicaStavka.id,
                ScanLog.created_at >= start_of_day,
            ),
        )
        .where(Zaduznica.created_at >= start_of_day)
        .group_by(UserAccount.id, UserAccount.first_name, UserAccount.last_name)
        .order_by(sa.desc("qty"))
        .limit(10)
    )

    leaderboard_rows = await session.execute(leaderboard_stmt)
    hours_since_start = max((now - start_of_day).total_seconds() / 3600, 1.0)
    leaderboard: list[LeaderboardEntry] = []
    for row in leaderboard_rows:
        total_tasks = _to_float(row.tasks_total)
        completed = _to_float(row.tasks_done)
        completion = (completed / total_tasks * 100) if total_tasks else 0.0
        speed = _to_float(row.qty) / hours_since_start
        full_name = f"{row.first_name} {row.last_name}"
        leaderboard.append(
            LeaderboardEntry(
                user_id=str(row.user_id),
                display_name=full_name,
                items_completed=int(row.qty or 0),
                task_completion=completion,
                speed_per_hour=speed,
            )
        )

    partial_items_subquery = (
        sa.select(sa.func.count())
        .select_from(TrebovanjeStavka)
        .where(
            TrebovanjeStavka.trebovanje_id == Trebovanje.id,
            TrebovanjeStavka.discrepancy_status != DiscrepancyStatus.none,
            TrebovanjeStavka.missing_qty > 0,
        )
        .scalar_subquery()
    )

    shortage_qty_subquery = (
        sa.select(sa.func.sum(sa.func.coalesce(TrebovanjeStavka.missing_qty, 0)))
        .select_from(TrebovanjeStavka)
        .where(
            TrebovanjeStavka.trebovanje_id == Trebovanje.id,
            TrebovanjeStavka.discrepancy_status != DiscrepancyStatus.none,
            TrebovanjeStavka.missing_qty > 0,
        )
        .scalar_subquery()
    )

    total_items_subquery = (
        sa.select(sa.func.count())
        .select_from(TrebovanjeStavka)
        .where(TrebovanjeStavka.trebovanje_id == Trebovanje.id)
        .scalar_subquery()
    )

    queue_stmt = (
        sa.select(
            Trebovanje.dokument_broj,
            Trebovanje.id,
            sa.func.min(Zaduznica.status).label("status"),
            sa.func.array_agg(sa.func.distinct(Zaduznica.magacioner_id)).label("assigned"),
            sa.func.max(Radnja.naziv).label("radnja"),
            total_items_subquery.label("total_items"),
            partial_items_subquery.label("partial_items"),
            shortage_qty_subquery.label("shortage_qty"),
        )
        .join(Zaduznica, Zaduznica.trebovanje_id == Trebovanje.id)
        .join(Radnja, Radnja.id == Trebovanje.radnja_id)
        .where(Zaduznica.status.in_([ZaduznicaStatus.assigned, ZaduznicaStatus.in_progress]))
        .group_by(Trebovanje.id)
        .order_by(Trebovanje.created_at)
        .limit(10)
    )
    queue_rows = await session.execute(queue_stmt)
    queue: list[QueueEntry] = []
    for row in queue_rows:
        assigned = [str(user_id) for user_id in (row.assigned or []) if user_id]
        shortage_qty_value = _to_float(row.shortage_qty or 0.0)
        queue.append(
            QueueEntry(
                dokument=row.dokument_broj,
                radnja=row.radnja,
                status=row.status.value if hasattr(row.status, "value") else str(row.status),
                assigned_to=assigned,
                total_items=int(row.total_items or 0),
                partial_items=int(row.partial_items or 0),
                shortage_qty=shortage_qty_value,
            )
        )

    total_tasks_today = await session.scalar(
        sa.select(sa.func.count()).select_from(Zaduznica).where(Zaduznica.created_at >= start_of_day)
    )
    done_tasks_today = await session.scalar(
        sa.select(sa.func.count())
        .select_from(Zaduznica)
        .where(Zaduznica.created_at >= start_of_day, Zaduznica.status == ZaduznicaStatus.done)
    )
    active_workers = await session.scalar(
        sa.select(sa.func.count(sa.func.distinct(Zaduznica.magacioner_id)))
        .where(Zaduznica.status == ZaduznicaStatus.in_progress)
    )

    shift_end_dt = datetime.combine(now.date(), SHIFT_END, tzinfo=timezone.utc)
    minutes_remaining = max((shift_end_dt - now).total_seconds() / 60, 0.0)

    partial_stats_stmt = (
        sa.select(
            sa.func.count(sa.distinct(TrebovanjeStavka.id)).label("partial_items"),
            sa.func.sum(sa.func.coalesce(TrebovanjeStavka.missing_qty, 0)).label("shortage_qty"),
        )
        .select_from(Zaduznica)
        .join(ZaduznicaStavka, ZaduznicaStavka.zaduznica_id == Zaduznica.id)
        .join(TrebovanjeStavka, TrebovanjeStavka.id == ZaduznicaStavka.trebovanje_stavka_id)
        .where(
            Zaduznica.created_at >= start_of_day,
            TrebovanjeStavka.discrepancy_status != DiscrepancyStatus.none,
            TrebovanjeStavka.missing_qty > 0,
        )
    )
    partial_stats_row = (await session.execute(partial_stats_stmt)).first()
    if partial_stats_row:
        partial_items_today = int(partial_stats_row.partial_items or 0)
        shortage_qty_value_today = _to_float(partial_stats_row.shortage_qty or 0.0)
    else:
        partial_items_today = 0
        shortage_qty_value_today = 0.0

    kpi = KpiSnapshot(
        total_tasks_today=int(total_tasks_today or 0),
        completed_percentage=float(
            (done_tasks_today or 0) / (total_tasks_today or 1) * 100
        ),
        active_workers=int(active_workers or 0),
        shift_ends_in_minutes=minutes_remaining,
        partial_items=partial_items_today,
        shortage_qty=shortage_qty_value_today,
    )

    return TvSnapshot(
        generated_at=now,
        leaderboard=leaderboard,
        queue=queue,
        kpi=kpi,
    )
