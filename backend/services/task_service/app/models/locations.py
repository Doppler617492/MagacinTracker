"""
Location models for warehouse topology (Zona → Regal → Polica → Bin)
Manhattan Active WMS - Enterprise location management
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List

import sqlalchemy as sa
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import LocationType
from .location import Magacin


class Location(Base):
    """
    Warehouse location in hierarchy (Zona → Regal → Polica → Bin)
    Self-referencing tree structure
    """
    __tablename__ = "locations"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    naziv: Mapped[str] = mapped_column(String(128), nullable=False)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    tip: Mapped[LocationType] = mapped_column(nullable=False, index=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True
    )
    magacin_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("magacin.id"),
        nullable=False,
        index=True
    )
    zona: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)  # Denormalized
    
    # Coordinates for map view
    x_coordinate: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    y_coordinate: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    
    # Capacity tracking
    capacity_max: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    capacity_current: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    
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
    magacin: Mapped[Magacin] = relationship("Magacin")
    parent: Mapped[Optional["Location"]] = relationship(
        "Location",
        remote_side=[id],
        back_populates="children"
    )
    children: Mapped[List["Location"]] = relationship(
        "Location",
        back_populates="parent",
        cascade="all, delete-orphan"
    )
    article_locations: Mapped[List["ArticleLocation"]] = relationship(
        "ArticleLocation",
        back_populates="location",
        cascade="all, delete-orphan"
    )
    
    @property
    def occupancy_percentage(self) -> float:
        """Calculate occupancy percentage"""
        if not self.capacity_max or self.capacity_max == 0:
            return 0.0
        return round((float(self.capacity_current) / float(self.capacity_max)) * 100, 2)
    
    @property
    def status_color(self) -> str:
        """Get color indicator based on occupancy"""
        occupancy = self.occupancy_percentage
        if occupancy >= 90:
            return "🔴"  # Full/red
        elif occupancy >= 50:
            return "🟡"  # Partial/yellow
        else:
            return "🟢"  # Available/green
    
    @property
    def full_path(self) -> str:
        """Get full path (e.g., ZONA A / REGAL A1 / POLICA A1-1 / BIN A1-1-01)"""
        if self.parent:
            return f"{self.parent.full_path} / {self.naziv}"
        return self.naziv
    
    @property
    def is_bin(self) -> bool:
        """Check if this is a bin (lowest level)"""
        return self.tip == LocationType.BIN
    
    def can_store(self, quantity: float) -> bool:
        """Check if location has capacity for quantity"""
        if not self.capacity_max:
            return True  # Unlimited capacity
        available = float(self.capacity_max) - float(self.capacity_current)
        return available >= quantity


class ArticleLocation(Base):
    """
    Article inventory by location
    Tracks which articles are in which bins
    """
    __tablename__ = "article_locations"
    __table_args__ = (
        sa.UniqueConstraint('artikal_id', 'location_id', name='uq_article_location'),
    )
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    artikal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=False,
        index=True
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=False,
        index=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    uom: Mapped[str] = mapped_column(String(32), nullable=False, default='PCS')
    last_counted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_moved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_primary_location: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
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
    location: Mapped[Location] = relationship("Location", back_populates="article_locations")


class CycleCount(Base):
    """Cycle count task for inventory accuracy verification"""
    __tablename__ = "cycle_counts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True,
        index=True
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='scheduled', index=True)
    count_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    location: Mapped[Optional[Location]] = relationship("Location")
    assigned_to: Mapped[Optional["UserAccount"]] = relationship("UserAccount")
    items: Mapped[List["CycleCountItem"]] = relationship(
        "CycleCountItem",
        back_populates="cycle_count",
        cascade="all, delete-orphan"
    )
    
    @property
    def accuracy_percentage(self) -> float:
        """Calculate count accuracy"""
        if not self.items:
            return 100.0
        
        items_with_variance = sum(1 for item in self.items if item.variance and abs(float(item.variance)) > 0)
        return round((1 - items_with_variance / len(self.items)) * 100, 2)


class CycleCountItem(Base):
    """Individual item in cycle count"""
    __tablename__ = "cycle_count_items"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_count_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cycle_counts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    artikal_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=False
    )
    system_quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    counted_quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    variance: Mapped[Decimal | None] = mapped_column(Numeric(12, 3), nullable=True)
    variance_percent: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    counted_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    counted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    cycle_count: Mapped[CycleCount] = relationship("CycleCount", back_populates="items")
    artikal: Mapped["Artikal"] = relationship("Artikal")
    location: Mapped[Location] = relationship("Location")
    counted_by: Mapped[Optional["UserAccount"]] = relationship("UserAccount")
    
    @property
    def is_discrepancy(self) -> bool:
        """Check if there's a counting discrepancy"""
        return self.variance is not None and abs(float(self.variance)) > 0
    
    @property
    def requires_recount(self) -> bool:
        """Check if variance exceeds threshold (5%)"""
        if self.variance_percent is None:
            return False
        return abs(float(self.variance_percent)) > 5.0


class PickRoute(Base):
    """Optimized picking route for zaduznica"""
    __tablename__ = "pick_routes"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    zaduznica_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("zaduznica.id"),
        nullable=False,
        index=True
    )
    route_data: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default='[]')
    total_distance_meters: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    zaduznica: Mapped["Zaduznica"] = relationship("Zaduznica")


class PutAwayTask(Base):
    """Put-away task for received items"""
    __tablename__ = "putaway_tasks"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receiving_item_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("receiving_item.id"),
        nullable=False,
        index=True
    )
    suggested_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True
    )
    actual_location_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("locations.id"),
        nullable=True
    )
    quantity: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='pending')
    assigned_to_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=sa.text('NOW()')
    )
    
    # Relationships
    receiving_item: Mapped["ReceivingItem"] = relationship("ReceivingItem")
    suggested_location: Mapped[Optional[Location]] = relationship("Location", foreign_keys=[suggested_location_id])
    actual_location: Mapped[Optional[Location]] = relationship("Location", foreign_keys=[actual_location_id])
    assigned_to: Mapped[Optional["UserAccount"]] = relationship("UserAccount")

