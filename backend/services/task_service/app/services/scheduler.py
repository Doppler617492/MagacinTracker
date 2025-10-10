from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import perf_counter
from typing import Optional

import redis.asyncio as aioredis
from prometheus_client import Histogram
from sqlalchemy import Select, case, func, select, cast, String
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.cache import get_redis

from ..models import SchedulerLog, Trebovanje, UserAccount, Zaduznica, ZaduznicaStavka
from ..models.enums import (
    AuditAction,
    SchedulerLogStatus,
    TrebovanjeStatus,
    ZaduznicaItemStatus,
    ZaduznicaStatus,
)
from ..services.audit import record_audit

SCHEDULER_LATENCY = Histogram("scheduler_latency_ms", "Scheduler latency in milliseconds")
LOCK_TTL_SECONDS = 600
LOCK_KEY_TEMPLATE = "scheduler:lock:{trebovanje_id}"


@dataclass(slots=True)
class SchedulerCandidate:
    user_id: uuid.UUID
    full_name: str
    active_tasks: int
    remaining_quantity: float

    @property
    def score(self) -> float:
        return float(self.remaining_quantity + self.active_tasks * 5)

    @property
    def reason(self) -> str:
        return f"Active tasks: {self.active_tasks}, Remaining qty: {self.remaining_quantity:.2f}"


class SchedulerLockManager:
    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client

    async def get_lock(self, trebovanje_id: uuid.UUID) -> Optional[uuid.UUID]:
        key = LOCK_KEY_TEMPLATE.format(trebovanje_id=str(trebovanje_id))
        value = await self._redis.get(key)
        if value:
            try:
                return uuid.UUID(value)
            except ValueError:
                await self._redis.delete(key)
        return None

    async def acquire_lock(self, trebovanje_id: uuid.UUID, log_id: uuid.UUID) -> None:
        key = LOCK_KEY_TEMPLATE.format(trebovanje_id=str(trebovanje_id))
        await self._redis.set(key, str(log_id), ex=LOCK_TTL_SECONDS)

    async def release_lock(self, trebovanje_id: uuid.UUID) -> None:
        key = LOCK_KEY_TEMPLATE.format(trebovanje_id=str(trebovanje_id))
        await self._redis.delete(key)


class SchedulerService:
    def __init__(self, session: AsyncSession, lock_manager: Optional[SchedulerLockManager] = None):
        self.session = session
        redis_client = get_redis() if lock_manager is None else None
        self.lock_manager = lock_manager or SchedulerLockManager(redis_client)

    async def suggest(self, trebovanje_id: uuid.UUID, actor_id: Optional[uuid.UUID] = None) -> tuple[SchedulerLog, bool]:
        start = perf_counter()
        existing_lock = await self.lock_manager.get_lock(trebovanje_id)
        if existing_lock:
            log = await self.session.get(SchedulerLog, existing_lock)
            if log:
                SCHEDULER_LATENCY.observe((perf_counter() - start) * 1000)
                return log, True
            await self.lock_manager.release_lock(trebovanje_id)

        trebovanje = await self.session.get(Trebovanje, trebovanje_id)
        if not trebovanje:
            raise ValueError("Trebovanje not found")
        if trebovanje.status == TrebovanjeStatus.done:
            raise ValueError("Trebovanje already completed")

        candidates = await self._load_candidates()
        if not candidates:
            raise ValueError("No available workers")

        best = min(candidates, key=lambda c: c.score)
        now = datetime.utcnow()
        log_entry = SchedulerLog(
            id=uuid.uuid4(),
            trebovanje_id=trebovanje_id,
            magacioner_id=best.user_id,
            status=SchedulerLogStatus.suggested,
            score=best.score,
            reason=best.reason,
            lock_expires_at=now + timedelta(seconds=LOCK_TTL_SECONDS),
            created_at=now,
            created_by_id=actor_id,
            details={
                "active_tasks": best.active_tasks,
                "remaining_quantity": best.remaining_quantity,
            },
        )
        self.session.add(log_entry)
        await self.session.commit()
        await self.lock_manager.acquire_lock(trebovanje_id, log_entry.id)
        await record_audit(
            self.session,
            action=AuditAction.scheduler_suggested,
            actor_id=actor_id,
            entity_type="trebovanje",
            entity_id=str(trebovanje_id),
            payload={
                "log_id": str(log_entry.id),
                "magacioner_id": str(best.user_id),
                "score": best.score,
                "reason": best.reason,
            },
        )
        SCHEDULER_LATENCY.observe((perf_counter() - start) * 1000)
        await self.session.commit()
        await self.session.refresh(log_entry)
        return log_entry, False

    async def cancel_suggestion(self, trebovanje_id: uuid.UUID, actor_id: Optional[uuid.UUID] = None) -> None:
        lock_id = await self.lock_manager.get_lock(trebovanje_id)
        if not lock_id:
            return

        log_entry = await self.session.get(SchedulerLog, lock_id)
        now = datetime.utcnow()

        if log_entry:
            log_entry.status = SchedulerLogStatus.override
            log_entry.lock_expires_at = now
            await record_audit(
                self.session,
                action=AuditAction.scheduler_override,
                actor_id=actor_id,
                entity_type="trebovanje",
                entity_id=str(trebovanje_id),
                payload={"log_id": str(log_entry.id), "action": "cancel"},
            )

        await self.lock_manager.release_lock(trebovanje_id)
        await self.session.commit()

    async def _load_candidates(self) -> list[SchedulerCandidate]:
        subquery: Select = (
            select(
                Zaduznica.magacioner_id.label("magacioner_id"),
                func.count().filter(Zaduznica.status != ZaduznicaStatus.done).label("active_tasks"),
                func.coalesce(
                    func.sum(
                        case(
                            (ZaduznicaStavka.status != ZaduznicaItemStatus.done,
                             ZaduznicaStavka.trazena_kolicina - ZaduznicaStavka.obradjena_kolicina),
                            else_=0,
                        )
                    ),
                    0,
                ).label("remaining_quantity"),
            )
            .join(Zaduznica.stavke)
            .group_by(Zaduznica.magacioner_id)
            .subquery()
        )

        query = (
            select(
                UserAccount.id,
                UserAccount.first_name,
                UserAccount.last_name,
                func.coalesce(subquery.c.active_tasks, 0),
                func.coalesce(subquery.c.remaining_quantity, 0.0),
            )
            .outerjoin(subquery, subquery.c.magacioner_id == UserAccount.id)
            .where(func.lower(cast(UserAccount.role, String)) == "magacioner", UserAccount.is_active.is_(True))
        )

        results = await self.session.execute(query)
        candidates: list[SchedulerCandidate] = []
        for row in results:
            candidates.append(
                SchedulerCandidate(
                    user_id=row[0],
                    full_name=f"{row[1]} {row[2]}",  # Construct full name from first_name and last_name
                    active_tasks=int(row[3] or 0),
                    remaining_quantity=float(row[4] or 0.0),
                )
            )
        return candidates
