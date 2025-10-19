"""
Pydantic schemas for location management
Manhattan Active WMS - Location API schemas
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from ..models.enums import LocationType


# ============================================================================
# Location Schemas
# ============================================================================

class LocationBase(BaseModel):
    """Base location schema"""
    naziv: str = Field(..., min_length=1, max_length=128, description="Location name")
    code: str = Field(..., min_length=1, max_length=32, description="Location code (unique)")
    tip: LocationType = Field(..., description="Location type")
    parent_id: Optional[UUID] = Field(None, description="Parent location ID")
    magacin_id: UUID = Field(..., description="Warehouse ID")
    zona: Optional[str] = Field(None, max_length=32, description="Zone code (denormalized)")
    x_coordinate: Optional[Decimal] = Field(None, description="X coordinate for map")
    y_coordinate: Optional[Decimal] = Field(None, description="Y coordinate for map")
    capacity_max: Optional[Decimal] = Field(None, description="Maximum capacity")
    is_active: bool = Field(True, description="Active status")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class LocationCreate(LocationBase):
    """Schema for creating location"""
    pass


class LocationUpdate(BaseModel):
    """Schema for updating location"""
    naziv: Optional[str] = Field(None, min_length=1, max_length=128)
    code: Optional[str] = Field(None, min_length=1, max_length=32)
    capacity_max: Optional[Decimal] = None
    x_coordinate: Optional[Decimal] = None
    y_coordinate: Optional[Decimal] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None


class LocationResponse(LocationBase):
    """Full location response"""
    id: UUID
    capacity_current: Decimal
    occupancy_percentage: float
    status_color: str
    full_path: str
    is_bin: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class LocationTreeNode(BaseModel):
    """Location tree node for hierarchy display"""
    id: UUID
    naziv: str
    code: str
    tip: LocationType
    capacity_max: Optional[Decimal]
    capacity_current: Decimal
    occupancy_percentage: float
    status_color: str
    is_active: bool
    children: List["LocationTreeNode"] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


# ============================================================================
# Article Location Schemas
# ============================================================================

class ArticleLocationBase(BaseModel):
    """Base article location schema"""
    artikal_id: UUID
    location_id: UUID
    quantity: Decimal
    uom: str = Field(default="PCS", max_length=32)
    is_primary_location: bool = Field(default=False)


class ArticleLocationCreate(ArticleLocationBase):
    """Schema for assigning article to location"""
    pass


class ArticleLocationUpdate(BaseModel):
    """Schema for updating article location quantity"""
    quantity: Decimal
    uom: Optional[str] = None
    is_primary_location: Optional[bool] = None


class ArticleLocationResponse(ArticleLocationBase):
    """Full article location response"""
    id: UUID
    last_counted_at: Optional[datetime]
    last_moved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ArticleInLocationDetail(BaseModel):
    """Article detail in location"""
    artikal_id: UUID
    sifra: str
    naziv: str
    quantity: Decimal
    uom: str
    is_primary_location: bool
    last_counted_at: Optional[datetime]


# ============================================================================
# Put-Away Schemas
# ============================================================================

class PutAwayLocationSuggestion(BaseModel):
    """Suggested location for put-away"""
    location_id: UUID
    location_code: str
    location_naziv: str
    score: float = Field(..., ge=0, le=100, description="Suggestion score (0-100)")
    distance_meters: Optional[float] = None
    available_capacity: Decimal
    occupancy_percentage: float
    reason: str = Field(..., description="Reason for suggestion (Serbian)")


class PutAwaySuggestRequest(BaseModel):
    """Request for put-away location suggestion"""
    artikal_id: UUID
    quantity: Decimal
    uom: str = Field(default="PCS")
    from_location_id: Optional[UUID] = Field(None, description="Starting location (dock)")


class PutAwaySuggestResponse(BaseModel):
    """Response with suggested locations"""
    artikal_id: UUID
    artikal_sifra: str
    artikal_naziv: str
    quantity: Decimal
    suggestions: List[PutAwayLocationSuggestion] = Field(..., description="Top 5 suggestions")


class PutAwayExecuteRequest(BaseModel):
    """Execute put-away to location"""
    receiving_item_id: UUID
    location_id: UUID
    quantity: Decimal
    override_suggestion: bool = Field(False, description="True if manually selected")


class PutAwayExecuteResponse(BaseModel):
    """Put-away execution result"""
    success: bool
    message: str
    article_location_id: Optional[UUID] = None
    new_occupancy_percentage: Optional[float] = None


# ============================================================================
# Pick Route Schemas
# ============================================================================

class PickTaskLocation(BaseModel):
    """Pick task with location"""
    stavka_id: UUID
    artikal_sifra: str
    artikal_naziv: str
    location_id: UUID
    location_code: str
    location_full_path: str
    quantity: Decimal
    sequence: int = Field(..., description="Pick sequence (1-based)")


class PickRouteResponse(BaseModel):
    """Optimized picking route"""
    zaduznica_id: UUID
    route_id: UUID
    tasks: List[PickTaskLocation] = Field(..., description="Tasks in optimal order")
    total_distance_meters: Optional[float] = None
    estimated_time_minutes: Optional[int] = None
    created_at: datetime


class PickRouteGenerateRequest(BaseModel):
    """Request to generate pick route"""
    zaduznica_id: UUID
    algorithm: str = Field(default="nearest_neighbor", description="'nearest_neighbor' or 'tsp'")


# ============================================================================
# Cycle Count Schemas
# ============================================================================

class CycleCountCreate(BaseModel):
    """Create cycle count task"""
    location_id: Optional[UUID] = Field(None, description="Specific location or None for zone")
    count_type: str = Field(..., description="'zone', 'regal', 'article', 'random'")
    scheduled_at: datetime
    assigned_to_id: Optional[UUID] = None


class CycleCountItemCount(BaseModel):
    """Count item in cycle count"""
    item_id: UUID
    counted_quantity: Decimal
    reason: Optional[str] = Field(None, description="Reason if variance exists")


class CycleCountComplete(BaseModel):
    """Complete cycle count"""
    counts: List[CycleCountItemCount]


class CycleCountItemResponse(BaseModel):
    """Cycle count item detail"""
    id: UUID
    artikal_id: UUID
    artikal_sifra: str
    artikal_naziv: str
    location_id: UUID
    location_code: str
    system_quantity: Decimal
    counted_quantity: Optional[Decimal]
    variance: Optional[Decimal]
    variance_percent: Optional[Decimal]
    is_discrepancy: bool
    requires_recount: bool
    reason: Optional[str]
    counted_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class CycleCountResponse(BaseModel):
    """Full cycle count response"""
    id: UUID
    location_id: Optional[UUID]
    location_code: Optional[str]
    location_naziv: Optional[str]
    scheduled_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    status: str
    count_type: Optional[str]
    accuracy_percentage: float
    items: List[CycleCountItemResponse] = Field(default_factory=list)
    created_at: datetime
    
    class Config:
        from_attributes = True


class CycleCountSummary(BaseModel):
    """Cycle count summary for list"""
    id: UUID
    location_code: Optional[str]
    count_type: Optional[str]
    scheduled_at: datetime
    status: str
    accuracy_percentage: float
    total_items: int
    discrepancies_count: int


# ============================================================================
# Warehouse Map Schemas
# ============================================================================

class WarehouseMapLocation(BaseModel):
    """Location for map view"""
    id: UUID
    code: str
    naziv: str
    tip: LocationType
    x: Decimal
    y: Decimal
    occupancy_percentage: float
    status_color: str
    is_active: bool


class WarehouseMapResponse(BaseModel):
    """Full warehouse map data"""
    magacin_id: UUID
    magacin_naziv: str
    locations: List[WarehouseMapLocation]
    zones: List[str] = Field(..., description="Available zones")
    last_updated: datetime

