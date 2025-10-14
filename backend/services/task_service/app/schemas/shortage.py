"""Pydantic schemas for shortage tracking and picking operations."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import DiscrepancyStatus


class PickByCodeRequest(BaseModel):
    """Request to record a pick using barcode or SKU."""
    code: str = Field(..., min_length=1, description="Barcode or SKU scanned/entered")
    quantity: float = Field(..., gt=0, description="Quantity picked")
    operation_id: str = Field(..., description="Idempotency key for offline sync")


class PickByCodeResponse(BaseModel):
    """Response after recording a pick."""
    stavka_id: UUID
    picked_qty: float
    required_qty: float
    missing_qty: float
    discrepancy_status: DiscrepancyStatus
    needs_barcode: bool
    matched_code: str  # The actual code that matched (barcode or sifra)
    message: str


class ShortPickRequest(BaseModel):
    """Request to record a short pick (less than requested)."""
    actual_qty: float = Field(..., ge=0, description="Actual quantity picked")
    reason: Optional[str] = Field(None, description="Reason for shortage")
    operation_id: str = Field(..., description="Idempotency key")


class ShortPickResponse(BaseModel):
    """Response after recording a short pick."""
    stavka_id: UUID
    picked_qty: float
    required_qty: float
    missing_qty: float
    discrepancy_status: DiscrepancyStatus
    message: str


class NotFoundRequest(BaseModel):
    """Request to mark an item as not found."""
    reason: Optional[str] = Field(None, description="Reason item was not found")
    operation_id: str = Field(..., description="Idempotency key")


class NotFoundResponse(BaseModel):
    """Response after marking item as not found."""
    stavka_id: UUID
    picked_qty: float
    required_qty: float
    discrepancy_status: DiscrepancyStatus
    message: str


class CompleteDocumentRequest(BaseModel):
    """Request to complete a document (trebovanje)."""
    confirm_incomplete: bool = Field(False, description="Confirm completion even with shortages")
    operation_id: str = Field(..., description="Idempotency key")


class CompleteDocumentResponse(BaseModel):
    """Response after completing a document."""
    trebovanje_id: UUID
    total_items: int
    completed_items: int
    items_with_shortages: int
    total_shortage_qty: float
    status: str
    message: str


class ShortageReportItem(BaseModel):
    """Single line in shortage report."""
    trebovanje_dokument_broj: str
    trebovanje_datum: str
    radnja_naziv: str
    magacin_naziv: str
    artikal_sifra: str
    artikal_naziv: str
    required_qty: float
    picked_qty: float
    missing_qty: float
    discrepancy_status: str
    discrepancy_reason: Optional[str]
    magacioner_name: str
    completed_at: Optional[str]


class ManualQuantityRequest(BaseModel):
    """Request for manual quantity entry (no barcode scanning)."""
    quantity: float = Field(..., ge=0, description="Quantity entered manually")
    close_item: bool = Field(False, description="Close item even if quantity < required")
    reason: Optional[str] = Field(None, description="Reason for shortage (mandatory if qty < required or close_item=true)")
    note: Optional[str] = Field(None, description="Optional additional note")
    operation_id: str = Field(..., description="Idempotency key for offline sync")


class ManualQuantityResponse(BaseModel):
    """Response after manual quantity entry."""
    stavka_id: UUID
    picked_qty: float
    required_qty: float
    missing_qty: float
    status: str  # "novo", "u_toku", "zatvoreno", "djelimicno"
    discrepancy_status: DiscrepancyStatus
    message: str

