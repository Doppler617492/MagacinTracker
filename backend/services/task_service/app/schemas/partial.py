"""
Pydantic schemas for Manhattan-style partial completion
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.enums import PartialCompletionReason


class PartialCompleteRequest(BaseModel):
    """
    Request for partial task completion
    Manhattan-style exception handling
    """
    stavka_id: UUID = Field(..., description="Trebovanje stavka ID")
    količina_pronađena: Decimal = Field(
        ..., 
        ge=0,
        description="Actual quantity found (Serbian: Količina pronađena)"
    )
    razlog: PartialCompletionReason = Field(
        ...,
        description="Reason for partial completion"
    )
    razlog_tekst: Optional[str] = Field(
        None,
        max_length=500,
        description="Custom reason text (required if razlog='drugo')"
    )
    operation_id: str = Field(
        ...,
        description="Idempotency key for offline queue"
    )
    
    @field_validator('razlog_tekst')
    @classmethod
    def validate_razlog_tekst(cls, v, info):
        """If razlog is 'drugo', razlog_tekst is required"""
        if info.data.get('razlog') == PartialCompletionReason.DRUGO and not v:
            raise ValueError(
                "razlog_tekst is required when razlog='drugo' (Obavezan tekst za 'Drugo')"
            )
        return v
    
    @field_validator('količina_pronađena')
    @classmethod
    def validate_količina(cls, v):
        """Količina must be >= 0"""
        if v < 0:
            raise ValueError("Količina ne može biti manja od 0")
        return v


class PartialCompleteResponse(BaseModel):
    """Response for partial completion"""
    stavka_id: UUID
    količina_tražena: Decimal
    količina_pronađena: Decimal
    razlog: PartialCompletionReason
    razlog_tekst: Optional[str]
    is_partial: bool
    procenat_ispunjenja: Decimal
    status: str
    status_serbian: str
    message: str
    completed_at: datetime
    completed_by: str
    
    class Config:
        from_attributes = True


class MarkirajPreostaloRequest(BaseModel):
    """
    Mark remaining quantity as 0 (not found/not available)
    Serbian: Markiraj preostalo = 0
    """
    stavka_id: UUID
    razlog: PartialCompletionReason
    razlog_tekst: Optional[str] = None
    operation_id: str
    
    @field_validator('razlog_tekst')
    @classmethod
    def validate_razlog_tekst(cls, v, info):
        """If razlog is 'drugo', razlog_tekst is required"""
        if info.data.get('razlog') == PartialCompletionReason.DRUGO and not v:
            raise ValueError(
                "razlog_tekst is required when razlog='drugo'"
            )
        return v


class TrebovanjeStavkaPartialInfo(BaseModel):
    """
    Extended trebovanje stavka info with partial completion data
    For Admin tables with % ispunjenja column
    """
    id: UUID
    artikl_sifra: str
    naziv: str
    količina_tražena: Decimal
    količina_pronađena: Optional[Decimal]
    picked_qty: Decimal
    missing_qty: Decimal
    is_partial: bool
    procenat_ispunjenja: Optional[Decimal]
    razlog: Optional[PartialCompletionReason]
    razlog_tekst: Optional[str]
    razlog_display: Optional[str]  # Localized reason text
    status: str
    status_serbian: str
    completed_at: Optional[datetime]
    completed_by_name: Optional[str]
    
    class Config:
        from_attributes = True


class TrebovanjeWithPartialStats(BaseModel):
    """
    Trebovanje summary with partial completion statistics
    For Admin table view
    """
    id: UUID
    dokument_broj: str
    datum: datetime
    status: str
    ukupno_stavki: int
    stavki_završeno: int
    stavki_djelimično: int
    ukupno_traženo: Decimal
    ukupno_pronađeno: Decimal
    procenat_ispunjenja: Decimal
    top_razlozi: list[dict]  # Top 3 reasons for partial completion
    
    class Config:
        from_attributes = True


class PartialCompletionStats(BaseModel):
    """
    Statistics for partial completions
    For KPI dashboard and TV display
    """
    period: str  # 'today', 'shift_a', 'shift_b', 'week', 'month'
    total_items: int
    fully_completed: int
    partially_completed: int
    partial_ratio: float
    top_reasons: list[dict]  # [{'razlog': '...', 'count': 5, 'percentage': 15.5}]
    by_worker: list[dict]  # Worker performance with partial stats
    by_team: list[dict]  # Team performance with partial stats
    
    class Config:
        from_attributes = True


# Reason display names in Serbian
REASON_DISPLAY_SR = {
    PartialCompletionReason.NEMA_NA_STANJU: "Nema na stanju",
    PartialCompletionReason.OSTECENO: "Oštećeno",
    PartialCompletionReason.NIJE_PRONAĐENO: "Nije pronađeno",
    PartialCompletionReason.KRIVI_ARTIKAL: "Krivi artikal",
    PartialCompletionReason.DRUGO: "Drugo"
}


def get_reason_display(reason: Optional[PartialCompletionReason], custom_text: Optional[str] = None) -> Optional[str]:
    """Get localized reason display text"""
    if not reason:
        return None
    
    base_text = REASON_DISPLAY_SR.get(reason, str(reason))
    
    if reason == PartialCompletionReason.DRUGO and custom_text:
        return f"{base_text}: {custom_text}"
    
    return base_text

