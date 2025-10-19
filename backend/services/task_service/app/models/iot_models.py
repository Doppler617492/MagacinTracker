"""
IoT Integration Layer models
Manhattan Active WMS - Phase 5
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import RFIDEventType, DoorStatus, TelemetryAlertSeverity


class RFIDEvent(Base):
    """
    RFID gateway events (entry/exit tracking)
    Zebra FX RFID readers, Impinj gateways, etc.
    """
    __tablename__ = "rfid_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    gateway_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    antenna_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    tag_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_type: Mapped[RFIDEventType] = mapped_column(nullable=False, default=RFIDEventType.READ)
    rssi: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Signal strength
    zone: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('NOW()')
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    @property
    def processing_latency_ms(self) -> Optional[int]:
        """Time from timestamp to processing (ms)"""
        if not self.processed_at:
            return None
        delta = self.processed_at - self.timestamp
        return int(delta.total_seconds() * 1000)


class RFIDTagBinding(Base):
    """
    RFID tag to entity binding (tag → prijem/otprema/lokacija)
    """
    __tablename__ = "rfid_tag_bindings"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tag_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    bound_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    bound_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('NOW()')
    )
    unbound_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default='true')
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    bound_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")


class Door(Base):
    """
    Industrial door/gate control (FALCON radar + BFT photocell)
    """
    __tablename__ = "doors"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    door_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    naziv: Mapped[str] = mapped_column(String(128), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True
    )
    zone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    current_status: Mapped[DoorStatus] = mapped_column(nullable=False, default=DoorStatus.CLOSED)
    last_command: Mapped[str | None] = mapped_column(String(32), nullable=True)
    last_command_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_command_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    safety_beam_status: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # True = clear, False = blocked
    radar_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    auto_close_timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    
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
    location: Mapped[Optional["Location"]] = relationship("Location")
    last_command_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")
    command_logs: Mapped[List["DoorCommandLog"]] = relationship("DoorCommandLog", back_populates="door")
    
    @property
    def is_safe_to_close(self) -> bool:
        """Check if safe to close (photocell clear)"""
        return self.safety_beam_status != False  # None or True is OK


class DoorCommandLog(Base):
    """Door command execution log"""
    __tablename__ = "door_command_log"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    door_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("doors.id"),
        nullable=False,
        index=True
    )
    command: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    requested_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('NOW()')
    )
    success: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    safety_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    door: Mapped[Door] = relationship("Door", back_populates="command_logs")
    requested_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")


class TelemetryData(Base):
    """Sensor telemetry data (temperature, humidity, battery, ping)"""
    __tablename__ = "telemetry_data"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    device_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    zone: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    temperature: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    humidity: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    vibration: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    battery_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ping_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('NOW()')
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )


class TelemetryAlert(Base):
    """Telemetry alerts (threshold violations)"""
    __tablename__ = "telemetry_alerts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    alert_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity: Mapped[TelemetryAlertSeverity] = mapped_column(nullable=False)
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    threshold_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    actual_value: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    raised_at: Mapped[datetime] = mapped_column(
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
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default='true')
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    acknowledged_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")


class VisionCountTask(Base):
    """Vision-based cycle count task (photo + manual confirmation)"""
    __tablename__ = "vision_count_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )
    artikal_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=True
    )
    system_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    counted_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    variance: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    photo_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default='[]')
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='pending', index=True)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    location: Mapped["Location"] = relationship("Location")
    artikal: Mapped[Optional["Artikal"]] = relationship("Artikal")
    assigned_to: Mapped[Optional["UserAccount"]] = relationship("UserAccount", foreign_keys=[assigned_to_id])
    reviewed_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount", foreign_keys=[reviewed_by_id])
    
    @property
    def has_variance(self) -> bool:
        """Check if variance exists"""
        return self.variance is not None and self.variance != 0
    
    @property
    def variance_percentage(self) -> Optional[float]:
        """Calculate variance percentage"""
        if self.system_quantity is None or self.system_quantity == 0:
            return None
        if self.variance is None:
            return None
        return float(self.variance) / float(self.system_quantity) * 100


class PhotoAttachment(Base):
    """Photo attachment for various entities"""
    __tablename__ = "photo_attachments"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    thumbnail_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    exif_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default='{}')
    uploaded_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=sa.text('NOW()')
    )
    comment: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    uploaded_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")
    
    @property
    def url(self) -> str:
        """Get photo URL (signed or public)"""
        # In production, this would return signed URL from S3/MinIO
        return f"/api/photos/{self.id}"
    
    @property
    def thumbnail_url(self) -> Optional[str]:
        """Get thumbnail URL"""
        if not self.thumbnail_path:
            return None
        return f"/api/photos/{self.id}/thumbnail"

