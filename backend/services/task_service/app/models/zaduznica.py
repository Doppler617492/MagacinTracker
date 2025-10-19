from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import TaskPriority, ZaduznicaItemStatus, ZaduznicaStatus


class Zaduznica(Base):
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trebovanje_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trebovanje.id", ondelete="CASCADE"), index=True
    )
    magacioner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("team.id"), nullable=True, index=True
    )
    prioritet: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="task_priority"), default=TaskPriority.normal
    )
    rok: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[ZaduznicaStatus] = mapped_column(
        Enum(ZaduznicaStatus, name="zaduznica_status"), default=ZaduznicaStatus.assigned
    )
    progress: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    stavke: Mapped[list["ZaduznicaStavka"]] = relationship(
        back_populates="zaduznica", cascade="all, delete-orphan"
    )

    trebovanje: Mapped["Trebovanje"] = relationship("Trebovanje")
    team: Mapped["Team"] = relationship("Team", foreign_keys=[team_id])


class ZaduznicaStavka(Base):
    __tablename__ = "zaduznica_stavka"
    __table_args__ = (
        CheckConstraint("trazena_kolicina > 0", name="trazena_kolicina_gt_zero"),
        CheckConstraint(
            "obradjena_kolicina <= trazena_kolicina", name="obradjena_le_trazena"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zaduznica_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("zaduznica.id", ondelete="CASCADE"), index=True
    )
    trebovanje_stavka_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trebovanje_stavka.id", ondelete="CASCADE"), index=True
    )
    trazena_kolicina: Mapped[float] = mapped_column(Numeric(12, 3))
    obradjena_kolicina: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    status: Mapped[ZaduznicaItemStatus] = mapped_column(
        Enum(ZaduznicaItemStatus, name="zaduznica_stavka_status"), default=ZaduznicaItemStatus.assigned
    )

    zaduznica: Mapped[Zaduznica] = relationship(back_populates="stavke")
    # trebovanje_stavka: Mapped["TrebovanjeStavka"] = relationship("TrebovanjeStavka", back_populates="zaduznica_stavke")
