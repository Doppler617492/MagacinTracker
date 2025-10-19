from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import DiscrepancyStatus, PartialCompletionReason, TrebovanjeItemStatus, TrebovanjeStatus
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
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    allow_incomplete_close: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    magacin: Mapped["Magacin"] = relationship("Magacin")
    radnja: Mapped["Radnja"] = relationship("Radnja")
    stavke: Mapped[list["TrebovanjeStavka"]] = relationship(
        back_populates="trebovanje", cascade="all, delete-orphan"
    )


class TrebovanjeStavka(Base):
    __tablename__ = "trebovanje_stavka"
    __table_args__ = (
        CheckConstraint("kolicina_trazena > 0", name="kolicina_trazena_gt_zero"),
        CheckConstraint(
            "kolicina_uradjena <= kolicina_trazena", name="kolicina_uradjena_le_trazena"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trebovanje_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trebovanje.id", ondelete="CASCADE")
    )
    artikal_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("artikal.id"))
    artikl_sifra: Mapped[str] = mapped_column(String(64))
    naziv: Mapped[str] = mapped_column(String(255))
    kolicina_trazena: Mapped[float] = mapped_column(Numeric(12, 3))
    kolicina_uradjena: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    barkod: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[TrebovanjeItemStatus] = mapped_column(
        Enum(TrebovanjeItemStatus, name="trebovanje_stavka_status"), default=TrebovanjeItemStatus.new
    )
    needs_barcode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Shortage tracking fields (existing)
    picked_qty: Mapped[float] = mapped_column(Numeric(12, 3), default=0, nullable=False)
    missing_qty: Mapped[float] = mapped_column(Numeric(12, 3), default=0, nullable=False)
    discrepancy_status: Mapped[DiscrepancyStatus] = mapped_column(
        Enum(DiscrepancyStatus, name="discrepancy_status_enum"), default=DiscrepancyStatus.none, nullable=False
    )
    discrepancy_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    last_scanned_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Partial completion fields (Manhattan-style exception handling)
    kolicina_pronađena: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    razlog: Mapped[PartialCompletionReason | None] = mapped_column(
        Enum(PartialCompletionReason, name="partial_completion_reason_enum"), nullable=True
    )
    razlog_tekst: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_partial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    procenat_ispunjenja: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    trebovanje: Mapped[Trebovanje] = relationship(back_populates="stavke")
    completed_by: Mapped["UserAccount"] = relationship("UserAccount", foreign_keys=[completed_by_id])
    # zaduznica_stavke: Mapped[list["ZaduznicaStavka"]] = relationship("ZaduznicaStavka", back_populates="trebovanje_stavka")
    
    @property
    def completion_percentage(self) -> float:
        """Calculate completion percentage"""
        if not self.kolicina_trazena or self.kolicina_trazena == 0:
            return 100.0
        if self.kolicina_pronađena is None:
            return 0.0
        return round((float(self.kolicina_pronađena) / float(self.kolicina_trazena)) * 100, 2)
    
    @property
    def is_fully_completed(self) -> bool:
        """Check if item is fully completed"""
        return (
            self.kolicina_pronađena is not None and 
            self.kolicina_pronađena >= self.kolicina_trazena
        )
    
    @property
    def status_serbian(self) -> str:
        """Get status in Serbian (for API responses)"""
        if self.is_partial:
            return "Završeno (djelimično)"
        elif self.status == TrebovanjeItemStatus.done:
            return "Završeno"
        elif self.status == TrebovanjeItemStatus.in_progress:
            return "U toku"
        elif self.status == TrebovanjeItemStatus.assigned:
            return "Dodijeljen"
        else:
            return "Nov"
