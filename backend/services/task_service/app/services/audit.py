from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models import AuditLog
from ..models.enums import AuditAction


async def record_audit(
    session: AsyncSession,
    *,
    action: AuditAction | str,
    actor_id: UUID | None,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any] | None = None,
) -> None:
    if isinstance(action, AuditAction):
        value = action.value
    elif isinstance(action, str):
        try:
            value = AuditAction[action].value
        except KeyError:
            value = action
    else:
        value = str(action)
    session.add(
        AuditLog(
            action=value,  # store DB enum label (e.g. "zaduznica.assigned")
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload or {},
        )
    )
