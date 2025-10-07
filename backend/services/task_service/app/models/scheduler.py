from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .enums import SchedulerLogStatus


class SchedulerLog(Base):
    __tablename__ = "scheduler_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trebovanje_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trebovanje.id", ondelete="CASCADE"))
    magacioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="CASCADE"))
    status: Mapped[SchedulerLogStatus] = mapped_column(default=SchedulerLogStatus.suggested)
    score: Mapped[float] = mapped_column()
    reason: Mapped[str] = mapped_column()
    lock_expires_at: Mapped[datetime | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user_account.id", ondelete="SET NULL"))
    details: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, default=dict)
