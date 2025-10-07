from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Artikal(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sifra: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    naziv: Mapped[str] = mapped_column(String(255))
    jedinica_mjere: Mapped[str] = mapped_column(String(32), default="kom")
    aktivan: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    barkodovi: Mapped[list["ArtikalBarkod"]] = relationship(
        back_populates="artikal", cascade="all, delete-orphan"
    )


class ArtikalBarkod(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artikal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artikal.id", ondelete="CASCADE"), index=True)
    barkod: Mapped[str] = mapped_column(String(64), unique=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    artikal: Mapped[Artikal] = relationship(back_populates="barkodovi")
