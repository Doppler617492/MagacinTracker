from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import TrebovanjeItemStatus, TrebovanjeStatus
from .location import Magacin, Radnja


class Trebovanje(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dokument_broj: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    datum: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    magacin_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("magacin.id"))
    radnja_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("radnja.id"))
    status: Mapped[TrebovanjeStatus] = mapped_column(
        Enum(TrebovanjeStatus, name="trebovanje_status"), default=TrebovanjeStatus.new
    )
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("user_account.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    magacin: Mapped["Magacin"] = relationship("Magacin")
    radnja: Mapped["Radnja"] = relationship("Radnja")
    stavke: Mapped[list["TrebovanjeStavka"]] = relationship(
        back_populates="trebovanje", cascade="all, delete-orphan"
    )


class TrebovanjeStavka(Base):
    __table_args__ = (
        CheckConstraint("kolicina_trazena > 0", name="kolicina_trazena_gt_zero"),
        CheckConstraint(
            "kolicina_uradjena <= kolicina_trazena", name="kolicina_uradjena_le_trazena"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trebovanje_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trebovanje.id", ondelete="CASCADE"))
    artikal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("artikal.id"))
    artikl_sifra: Mapped[str] = mapped_column(String(64))
    naziv: Mapped[str] = mapped_column(String(255))
    kolicina_trazena: Mapped[float] = mapped_column(Numeric(12, 3))
    kolicina_uradjena: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    status: Mapped[TrebovanjeItemStatus] = mapped_column(
        Enum(TrebovanjeItemStatus, name="trebovanje_stavka_status"), default=TrebovanjeItemStatus.new
    )
    needs_barcode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    trebovanje: Mapped[Trebovanje] = relationship(back_populates="stavke")
