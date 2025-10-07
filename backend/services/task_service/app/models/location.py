from __future__ import annotations

import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Magacin(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pantheon_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    naziv: Mapped[str] = mapped_column(String(255))


class Radnja(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pantheon_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    naziv: Mapped[str] = mapped_column(String(255))
