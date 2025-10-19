"""
Document models for Pantheon ERP integration (Receipts & Dispatches)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .enums import DocumentDirection, DocumentItemStatus


class DocType(Base):
    """
    Document Type (synchronized from Pantheon)
    """
    __tablename__ = "doc_types"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    direction: Mapped[DocumentDirection] = mapped_column(index=True)
    aktivan: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Receipt(Base):
    """
    Inbound/Receipt Document (from Pantheon GetReceiptDocWMS)
    """
    __tablename__ = "receipts"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_no: Mapped[str] = mapped_column(String(64), index=True)
    doc_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doc_types.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # Parties
    supplier_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("subjects.id"), 
        nullable=True
    )
    store_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("subjects.id"), 
        nullable=True
    )
    
    # Metadata
    responsible_person: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    header_ref: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Sync tracking
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    doc_type: Mapped[DocType] = relationship()
    supplier: Mapped[Optional["Subject"]] = relationship(foreign_keys=[supplier_id])
    store: Mapped[Optional["Subject"]] = relationship(foreign_keys=[store_id])
    items: Mapped[list["ReceiptItem"]] = relationship(
        back_populates="receipt",
        cascade="all, delete-orphan"
    )
    
    # Unique constraint on doc_no + doc_type_id + date
    __table_args__ = (
        {'comment': 'Inbound receipt documents from Pantheon ERP'},
    )


class ReceiptItem(Base):
    """
    Receipt Document Item
    """
    __tablename__ = "receipt_items"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    receipt_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("receipts.id", ondelete="CASCADE"),
        index=True
    )
    
    # Article reference (nullable for lookup failures)
    article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=True,
        index=True
    )
    
    # Raw data from Pantheon
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(32))
    barcode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Quantities
    qty_requested: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    qty_completed: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    
    # Status & reason
    status: Mapped[DocumentItemStatus] = mapped_column(default=DocumentItemStatus.NEW)
    reason_missing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    receipt: Mapped[Receipt] = relationship(back_populates="items")
    article: Mapped[Optional["Artikal"]] = relationship()


class Dispatch(Base):
    """
    Outbound/Dispatch Document (from Pantheon GetIssueDocWMS)
    """
    __tablename__ = "dispatches"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doc_no: Mapped[str] = mapped_column(String(64), index=True)
    doc_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("doc_types.id"))
    date: Mapped[date] = mapped_column(Date, index=True)
    
    # Parties
    warehouse_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id"),
        nullable=True
    )
    issuer: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    receiver: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    
    # Metadata
    responsible_person: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    header_ref: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Sync tracking
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    doc_type: Mapped[DocType] = relationship()
    warehouse: Mapped[Optional["Subject"]] = relationship()
    items: Mapped[list["DispatchItem"]] = relationship(
        back_populates="dispatch",
        cascade="all, delete-orphan"
    )


class DispatchItem(Base):
    """
    Dispatch Document Item
    """
    __tablename__ = "dispatch_items"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dispatch_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("dispatches.id", ondelete="CASCADE"),
        index=True
    )
    
    # Article reference
    article_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("artikal.id"),
        nullable=True,
        index=True
    )
    
    # Raw data from Pantheon
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str] = mapped_column(String(32))
    barcode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    
    # Quantities
    qty_requested: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    qty_completed: Mapped[Decimal] = mapped_column(Numeric(12, 3), default=0)
    
    # WMS flags (critical for task creation)
    exists_in_wms: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    wms_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    warehouse_code: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Status & reason
    status: Mapped[DocumentItemStatus] = mapped_column(default=DocumentItemStatus.NEW)
    reason_missing: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    dispatch: Mapped[Dispatch] = relationship(back_populates="items")
    article: Mapped[Optional["Artikal"]] = relationship()

