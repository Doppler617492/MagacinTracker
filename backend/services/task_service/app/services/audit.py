from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog
from ..models.enums import AuditAction


async def record_audit(
    session: AsyncSession,
    *,
    action: AuditAction,
    actor_id: UUID | None,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    session.add(
        AuditLog(
            action=action,
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )
    )
