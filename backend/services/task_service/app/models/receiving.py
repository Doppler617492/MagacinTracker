"""
Receiving (Prijem robe) models for inbound workflow
Manhattan Active WMS style with exception handling
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional, List

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import ReceivingStatus, ReceivingReason, ReceivingItemStatus
from .location import Magacin
from .subject import Subject
from .user import UserAccount


class ReceivingHeader(Base):
    """
    Receiving document header (Prijem robe)
    Manhattan-style inbound workflow
    """
    __tablename__ = "receiving_header"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    broj_prijema: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    dobavljac_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=True
    )
    magacin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("magacin.id"),
        nullable=False
    )
    datum: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[ReceivingStatus] = mapped_column(nullable=False, default=ReceivingStatus.NOVO, index=True)
    
    # Audit trail
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}')
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    dobavljac: Mapped[Optional[Subject]] = relationship("Subject", foreign_keys=[dobavljac_id])
    magacin: Mapped[Magacin] = relationship("Magacin")
    items: Mapped[List[ReceivingItem]] = relationship(
        "ReceivingItem",
        back_populates="header",
        cascade="all, delete-orphan"
    )
    created_by: Mapped[Optional[UserAccount]] = relationship("UserAccount", foreign_keys=[created_by_id])
    started_by: Mapped[Optional[UserAccount]] = relationship("UserAccount", foreign_keys=[started_by_id])
    completed_by: Mapped[Optional[UserAccount]] = relationship("UserAccount", foreign_keys=[completed_by_id])
    
    @property
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        if not self.items:
            return 0.0
        
        total_trazena = sum(float(item.kolicina_trazena) for item in self.items)
        total_primljena = sum(float(item.kolicina_primljena) for item in self.items)
        
        if total_trazena == 0:
            return 100.0
        
        return round((total_primljena / total_trazena) * 100, 2)
    
    @property
    def is_partial(self) -> bool:
        """Check if any items have discrepancies"""
        return any(
            item.kolicina_primljena != item.kolicina_trazena
            for item in self.items
        )
    
    @property
    def status_serbian(self) -> str:
        """Get status in Serbian"""
        status_map = {
            ReceivingStatus.NOVO: "Novo",
            ReceivingStatus.U_TOKU: "U toku",
            ReceivingStatus.ZAVRSENO: "Završeno",
            ReceivingStatus.ZAVRSENO_DJELIMICNO: "Završeno (djelimično)"
        }
        return status_map.get(self.status, str(self.status))


class ReceivingItem(Base):
    """
    Receiving document item (Stavka prijema)
    """
    __tablename__ = "receiving_item"
    __table_args__ = (
        CheckConstraint("kolicina_trazena > 0", name="ck_receiving_item_trazena_gt_zero"),
        CheckConstraint("kolicina_primljena >= 0", name="ck_receiving_item_primljena_ge_zero"),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    header_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("receiving_header.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    artikal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=True
    )
    sifra: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    naziv: Mapped[str] = mapped_column(String(255), nullable=False)
    jedinica_mjere: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # Quantities (always in base_uom - PCS)
    kolicina_trazena: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    kolicina_primljena: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0, server_default='0')
    
    # Exception handling (Manhattan pattern)
    razlog: Mapped[ReceivingReason | None] = mapped_column(nullable=True)
    napomena: Mapped[str | None] = mapped_column(Text, nullable=True)
    attachments: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default='[]')
    
    # Status
    status: Mapped[ReceivingItemStatus] = mapped_column(
        nullable=False,
        default=ReceivingItemStatus.NOVO,
        server_default='novo'
    )
    
    # Completion tracking
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    header: Mapped[ReceivingHeader] = relationship("ReceivingHeader", back_populates="items")
    artikal: Mapped[Optional["Artikal"]] = relationship("Artikal")
    completed_by: Mapped[Optional[UserAccount]] = relationship("UserAccount", foreign_keys=[completed_by_id])
    
    @property
    def completion_percentage(self) -> float:
        """Calculate item completion percentage"""
        if self.kolicina_trazena == 0:
            return 100.0
        return round((float(self.kolicina_primljena) / float(self.kolicina_trazena)) * 100, 2)
    
    @property
    def is_partial(self) -> bool:
        """Check if item received partially"""
        return (
            self.kolicina_primljena > 0 and
            self.kolicina_primljena < self.kolicina_trazena
        )
    
    @property
    def is_overage(self) -> bool:
        """Check if received more than expected"""
        return self.kolicina_primljena > self.kolicina_trazena
    
    @property
    def variance(self) -> float:
        """Calculate variance (primljena - trazena)"""
        return float(self.kolicina_primljena) - float(self.kolicina_trazena)
    
    @property
    def has_photos(self) -> bool:
        """Check if item has photo attachments"""
        return len(self.attachments) > 0
    
    @property
    def razlog_serbian(self) -> Optional[str]:
        """Get reason in Serbian"""
        if not self.razlog:
            return None
        
        reason_map = {
            ReceivingReason.MANJAK: "Manjak",
            ReceivingReason.VISAK: "Višak",
            ReceivingReason.OSTECENO: "Oštećeno",
            ReceivingReason.NIJE_ISPORUCENO: "Nije isporučeno",
            ReceivingReason.DRUGO: "Drugo"
        }
        return reason_map.get(self.razlog, str(self.razlog))

