"""
Pydantic schemas for AI Intelligence Layer
Manhattan Active WMS - Phase 4
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# AI Bin Allocation Schemas
# ============================================================================

class BinSuggestionRequest(BaseModel):
    """Request for AI bin suggestions"""
    receiving_item_id: UUID
    artikal_id: UUID
    quantity: Decimal
    magacin_id: UUID


class BinSuggestionItem(BaseModel):
    """Single bin suggestion"""
    rank: int = Field(..., ge=1, le=3, description="Rank (1-3)")
    location_id: str
    location_code: str
    location_path: str
    score: float = Field(..., ge=0, le=100, description="Score (0-100)")
    confidence: float = Field(..., ge=0, le=1, description="Confidence (0-1)")
    reason: str = Field(..., description="Reason in Serbian")
    available_capacity: float
    occupancy_percentage: float


class BinSuggestionResponse(BaseModel):
    """Response with AI bin suggestions"""
    suggestions: List[BinSuggestionItem]
    model_version: str
    latency_ms: int


class BinAcceptRequest(BaseModel):
    """Accept bin suggestion"""
    receiving_item_id: UUID
    location_id: UUID


class BinRejectRequest(BaseModel):
    """Reject bin suggestion"""
    receiving_item_id: UUID
    reason: str


# ============================================================================
# AI Restocking Schemas
# ============================================================================

class RestockSuggestionRequest(BaseModel):
    """Request for restocking suggestions"""
    magacin_id: UUID
    horizon_days: int = Field(default=7, ge=1, le=30, description="Forecast horizon (7-14 days)")


class RestockSuggestionItem(BaseModel):
    """Single restocking suggestion"""
    id: str
    article_code: str
    article_name: str
    current_stock: float
    suggested_quantity: float
    target_zone: str
    confidence: float = Field(..., ge=0, le=1)
    reason: str
    deadline: datetime


class RestockSuggestionResponse(BaseModel):
    """Response with restocking suggestions"""
    suggestions: List[RestockSuggestionItem]
    total_count: int
    model_version: str


class RestockApproveRequest(BaseModel):
    """Approve restocking suggestion"""
    suggestion_ids: List[UUID] = Field(..., min_items=1)


class RestockRejectRequest(BaseModel):
    """Reject restocking suggestion"""
    suggestion_id: UUID
    reason: str


# ============================================================================
# AI Anomaly Schemas
# ============================================================================

class AnomalyListItem(BaseModel):
    """Anomaly list item"""
    id: UUID
    type: str
    severity: str
    status: str
    title: str
    description: Optional[str]
    confidence: Decimal
    detected_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]


class AnomalyDetailResponse(BaseModel):
    """Detailed anomaly response"""
    id: UUID
    type: str
    severity: str
    status: str
    entity_type: Optional[str]
    entity_id: Optional[UUID]
    title: str
    description: Optional[str]
    details: dict
    confidence: Decimal
    detected_at: datetime
    acknowledged_by_id: Optional[UUID]
    acknowledged_at: Optional[datetime]
    resolved_by_id: Optional[UUID]
    resolved_at: Optional[datetime]
    resolution_note: Optional[str]
    time_to_acknowledge: Optional[float]
    time_to_resolve: Optional[float]


class AnomalyAckRequest(BaseModel):
    """Acknowledge anomaly"""
    pass  # No body needed, just anomaly_id in path


class AnomalyResolveRequest(BaseModel):
    """Resolve anomaly"""
    resolution_note: str = Field(..., min_length=5, max_length=500)


# ============================================================================
# Smart KPI Schemas
# ============================================================================

class ShiftSummaryResponse(BaseModel):
    """Shift summary statistics"""
    shift_name: str  # "Smena A (08-15)" or "Smena B (12-19)"
    date: str
    tasks_completed: int
    tasks_partial: int
    avg_completion_time_minutes: float
    picks_per_hour: float
    accuracy_percentage: float
    workers_count: int


class TeamComparisonItem(BaseModel):
    """Team comparison item"""
    team_name: str
    period_label: str  # "2025-10-19 do 2025-10-26"
    total_tasks: int
    tasks_completed: int
    completion_rate: float
    avg_time_per_task_minutes: float
    productivity_score: float  # 0-100


class TeamComparisonResponse(BaseModel):
    """Team vs team comparison"""
    teams: List[TeamComparisonItem]
    period_from: str
    period_to: str


class BinHeatmapItem(BaseModel):
    """Bin heatmap data point"""
    location_id: str
    location_code: str
    occupancy_percentage: float
    turnover_rate: float  # picks per day
    avg_pick_time_seconds: float
    problem_score: float  # 0-100 (higher = more problematic)


class BinHeatmapResponse(BaseModel):
    """Bin heatmap data"""
    bins: List[BinHeatmapItem]
    zona: Optional[str]
    total_count: int

