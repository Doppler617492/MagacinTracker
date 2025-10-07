from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CatalogSyncStatus(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payload_hash: Mapped[str | None]
    source: Mapped[str | None]
    executed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    processed: Mapped[int] = mapped_column(default=0)
    created: Mapped[int] = mapped_column(default=0)
    updated: Mapped[int] = mapped_column(default=0)
    deactivated: Mapped[int] = mapped_column(default=0)
    duration_ms: Mapped[float] = mapped_column(default=0.0)
    status: Mapped[str] = mapped_column(default="success")
    message: Mapped[str | None]
    finished_at: Mapped[datetime | None]
