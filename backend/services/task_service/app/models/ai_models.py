"""
AI Intelligence Layer models
Manhattan Active WMS - Phase 4
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import AnomalySeverity, AnomalyStatus


class AIAnomaly(Base):
    """
    AI-detected anomalies in warehouse operations
    Types: stock_drift, scan_mismatch, task_latency
    """
    __tablename__ = "ai_anomalies"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[AnomalySeverity] = mapped_column(nullable=False, index=True)
    status: Mapped[AnomalyStatus] = mapped_column(nullable=False, default=AnomalyStatus.NEW, server_default='new', index=True)
    entity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False, default=1.0)
    
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('NOW()')
    )
    acknowledged_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    
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
    acknowledged_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount", foreign_keys=[acknowledged_by_id])
    resolved_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount", foreign_keys=[resolved_by_id])
    
    @property
    def time_to_acknowledge(self) -> Optional[float]:
        """Time from detection to acknowledgment (hours)"""
        if not self.acknowledged_at:
            return None
        delta = self.acknowledged_at - self.detected_at
        return delta.total_seconds() / 3600.0
    
    @property
    def time_to_resolve(self) -> Optional[float]:
        """Time from detection to resolution (hours)"""
        if not self.resolved_at:
            return None
        delta = self.resolved_at - self.detected_at
        return delta.total_seconds() / 3600.0


class AIBinSuggestion(Base):
    """AI bin allocation suggestion log"""
    __tablename__ = "ai_bin_suggestions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receiving_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("receiving_item.id"),
        nullable=False,
        index=True
    )
    artikal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=False
    )
    suggested_location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=False
    )
    rank: Mapped[int] = mapped_column(Integer, nullable=False)  # 1, 2, 3
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)  # 0-100
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)  # 0.0-1.0
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    
    accepted: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    accepted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default='heuristic_v1')
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    receiving_item: Mapped["ReceivingItem"] = relationship("ReceivingItem")
    artikal: Mapped["Artikal"] = relationship("Artikal")
    suggested_location: Mapped["Location"] = relationship("Location")
    accepted_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")


class AIRestockSuggestion(Base):
    """AI predictive restocking suggestion"""
    __tablename__ = "ai_restock_suggestions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artikal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=False,
        index=True
    )
    magacin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("magacin.id"),
        nullable=False
    )
    current_stock: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    suggested_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    target_zone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    target_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True
    )
    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    horizon_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='pending', index=True)
    approved_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    trebovanje_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trebovanje.id"),
        nullable=True
    )
    
    model_version: Mapped[str] = mapped_column(String(32), nullable=False, default='ema_v1')
    
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
    artikal: Mapped["Artikal"] = relationship("Artikal")
    magacin: Mapped["Magacin"] = relationship("Magacin")
    target_location: Mapped[Optional["Location"]] = relationship("Location")
    approved_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")
    trebovanje: Mapped[Optional["Trebovanje"]] = relationship("Trebovanje")


class AIModelMetadata(Base):
    """AI model versioning and performance tracking"""
    __tablename__ = "ai_model_metadata"
    __table_args__ = (
        sa.UniqueConstraint('model_name', 'model_version', name='uq_model_name_version'),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_version: Mapped[str] = mapped_column(String(32), nullable=False)
    model_type: Mapped[str] = mapped_column(String(64), nullable=False)
    parameters: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    performance_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )

