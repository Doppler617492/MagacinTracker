"""
Pydantic schemas for Receiving (Prijem robe)
Manhattan Active WMS inbound workflow
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.enums import ReceivingStatus, ReceivingReason, ReceivingItemStatus


# ============================================================================
# REQUEST SCHEMAS
# ============================================================================

class ImportReceivingRequest(BaseModel):
    """Request for importing receiving from CSV/XLSX"""
    filename: str
    rows: List[dict]
    skip_duplicates: bool = Field(default=True, description="Skip duplicate broj_prijema")


class StartReceivingRequest(BaseModel):
    """Request to start receiving (set status to u_toku)"""
    operation_id: str = Field(..., description="Idempotency key")


class ReceiveItemRequest(BaseModel):
    """
    Request to receive an item
    Serbian: Primi stavku
    """
    quantity: Decimal = Field(..., ge=0, description="Količina primljena")
    razlog: Optional[ReceivingReason] = Field(None, description="Razlog za odstupanje")
    napomena: Optional[str] = Field(None, max_length=1000, description="Napomena")
    photo_ids: Optional[List[str]] = Field(default=None, description="Photo attachment IDs")
    operation_id: str = Field(..., description="Idempotency key")
    
    @field_validator('napomena')
    @classmethod
    def validate_napomena_for_drugo(cls, v, info):
        """If razlog is 'drugo', napomena should be provided"""
        if info.data.get('razlog') == ReceivingReason.DRUGO and not v:
            raise ValueError("Napomena je obavezna za razlog 'Drugo'")
        return v


class CompleteReceivingRequest(BaseModel):
    """Request to complete receiving"""
    confirm_partial: bool = Field(
        default=True,
        description="Confirm if OK to complete with partial quantities"
    )
    operation_id: str = Field(..., description="Idempotency key")


class UploadPhotoRequest(BaseModel):
    """Request to upload photo"""
    base64_data: str = Field(..., description="Base64 encoded image")
    filename: str = Field(..., max_length=255)
    receiving_item_id: UUID


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class ReceivingItemResponse(BaseModel):
    """Receiving item response"""
    id: UUID
    sifra: str
    naziv: str
    jedinica_mjere: str
    kolicina_trazena: Decimal
    kolicina_primljena: Decimal
    razlog: Optional[ReceivingReason]
    razlog_serbian: Optional[str]
    napomena: Optional[str]
    attachments: List[str]
    status: ReceivingItemStatus
    completion_percentage: float
    is_partial: bool
    is_overage: bool
    variance: float
    has_photos: bool
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ReceivingHeaderResponse(BaseModel):
    """Receiving header response"""
    id: UUID
    broj_prijema: str
    dobavljac_id: Optional[UUID]
    dobavljac_naziv: Optional[str]
    magacin_id: UUID
    magacin_naziv: str
    datum: date
    status: ReceivingStatus
    status_serbian: str
    completion_percentage: float
    is_partial: bool
    total_items: int
    items_received: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class ReceivingDetailResponse(BaseModel):
    """Detailed receiving response with items"""
    header: ReceivingHeaderResponse
    items: List[ReceivingItemResponse]
    
    class Config:
        from_attributes = True


class ReceiveItemResponse(BaseModel):
    """Response after receiving an item"""
    item_id: UUID
    kolicina_primljena: Decimal
    kolicina_trazena: Decimal
    variance: float
    razlog: Optional[ReceivingReason]
    completion_percentage: float
    status: ReceivingItemStatus
    message: str
    
    class Config:
        from_attributes = True


class CompleteReceivingResponse(BaseModel):
    """Response after completing receiving"""
    receiving_id: UUID
    broj_prijema: str
    status: ReceivingStatus
    total_items: int
    items_full: int
    items_partial: int
    items_overage: int
    completion_percentage: float
    message: str
    completed_at: datetime
    
    class Config:
        from_attributes = True


class UploadPhotoResponse(BaseModel):
    """Response after uploading photo"""
    photo_id: str
    url: str
    thumbnail_url: str
    
    class Config:
        from_attributes = True


class ImportReceivingResponse(BaseModel):
    """Response after importing receiving"""
    success: bool
    imported_count: int
    skipped_count: int
    error_count: int
    errors: List[dict]
    receiving_ids: List[UUID]
    
    class Config:
        from_attributes = True


# ============================================================================
# STATISTICS & REPORTS
# ============================================================================

class ReceivingStats(BaseModel):
    """Statistics for receiving operations"""
    period: str  # 'today', 'week', 'month'
    total_receivings: int
    completed_full: int
    completed_partial: int
    partial_ratio: float
    top_reasons: List[dict]  # Top reasons for discrepancies
    by_dobavljac: List[dict]  # Stats by supplier
    by_magacin: List[dict]  # Stats by warehouse
    
    class Config:
        from_attributes = True

