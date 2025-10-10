from __future__ import annotations

from datetime import datetime, time, timezone
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Radnja, ScanLog, Trebovanje, UserAccount, Zaduznica, ZaduznicaStavka
from ..models.enums import ZaduznicaStatus
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

    queue_stmt = (
        sa.select(
            Trebovanje.dokument_broj,
            Trebovanje.id,
            sa.func.min(Zaduznica.status).label("status"),
            sa.func.array_agg(sa.func.distinct(Zaduznica.magacioner_id)).label("assigned"),
            sa.func.max(Radnja.naziv).label("radnja"),
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
        queue.append(
            QueueEntry(
                dokument=row.dokument_broj,
                radnja=row.radnja,
                status=row.status.value if hasattr(row.status, "value") else str(row.status),
                assigned_to=assigned,
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

    kpi = KpiSnapshot(
        total_tasks_today=int(total_tasks_today or 0),
        completed_percentage=float(
            (done_tasks_today or 0) / (total_tasks_today or 1) * 100
        ),
        active_workers=int(active_workers or 0),
        shift_ends_in_minutes=minutes_remaining,
    )

    return TvSnapshot(
        generated_at=now,
        leaderboard=leaderboard,
        queue=queue,
        kpi=kpi,
    )
