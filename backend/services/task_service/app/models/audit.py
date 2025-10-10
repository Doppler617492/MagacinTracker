from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import AuditAction


class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    action: Mapped[AuditAction] = mapped_column(
        Enum(AuditAction, name="audit_action", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)  # IPv6 compatible
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
