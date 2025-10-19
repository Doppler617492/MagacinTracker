from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Artikal(Base):
    """
    Article/Product model (synchronized from Pantheon ERP via getIdentWMS)
    """
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sifra: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    naziv: Mapped[str] = mapped_column(String(255))
    jedinica_mjere: Mapped[str] = mapped_column(String(32), default="kom")
    aktivan: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Pantheon ERP fields
    supplier: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    article_class: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Sync tracking
    time_chg_ts: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    source: Mapped[str] = mapped_column(String(32), default="PANTHEON")  # PANTHEON or MANUAL
    
    barkodovi: Mapped[list["ArtikalBarkod"]] = relationship(
        back_populates="artikal", cascade="all, delete-orphan"
    )


class ArtikalBarkod(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artikal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("artikal.id", ondelete="CASCADE"), index=True)
    barkod: Mapped[str] = mapped_column(String(64), unique=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    artikal: Mapped[Artikal] = relationship(back_populates="barkodovi")
