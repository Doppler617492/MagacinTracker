"""
Location management API endpoints
Manhattan Active WMS - Location-Based WMS
"""
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, require_role
from ..models.enums import Role, LocationType
from ..schemas.locations import (
    LocationCreate,
    LocationUpdate,
    LocationResponse,
    LocationTreeNode,
    ArticleLocationCreate,
    ArticleLocationUpdate,
    ArticleLocationResponse,
    ArticleInLocationDetail,
    PutAwaySuggestRequest,
    PutAwaySuggestResponse,
    PutAwayExecuteRequest,
    PutAwayExecuteResponse,
    PickRouteGenerateRequest,
    PickRouteResponse,
    CycleCountCreate,
    CycleCountResponse,
    CycleCountComplete,
    CycleCountSummary,
    WarehouseMapResponse,
)
from ..services.location_service import LocationService
from ..services.putaway_service import PutAwayService
from ..services.picking_service import PickingService
from ..services.cycle_count_service import CycleCountService

router = APIRouter(prefix="/locations", tags=["Locations"])


# ============================================================================
# Location CRUD
# ============================================================================

@router.get("", response_model=List[LocationResponse])
async def get_locations(
    magacin_id: Optional[uuid.UUID] = None,
    zona: Optional[str] = None,
    tip: Optional[LocationType] = None,
    is_active: Optional[bool] = None,
    parent_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Get locations with filters"""
    locations = await LocationService.get_locations(
        db=db,
        magacin_id=magacin_id,
        zona=zona,
        tip=tip,
        is_active=is_active,
        parent_id=parent_id
    )
    return [LocationResponse.model_validate(loc) for loc in locations]


@router.get("/tree", response_model=List[LocationTreeNode])
async def get_location_tree(
    magacin_id: uuid.UUID,
    zona: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Get location hierarchy as tree structure"""
    tree = await LocationService.get_location_tree(db=db, magacin_id=magacin_id, zona=zona)
    return tree


@router.get("/{location_id}", response_model=LocationResponse)
async def get_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Get location by ID"""
    location = await LocationService.get_location_by_id(db=db, location_id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Lokacija ne postoji")
    return LocationResponse.model_validate(location)


@router.post("", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(
    data: LocationCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER]))
):
    """Create new location"""
    try:
        location = await LocationService.create_location(db=db, data=data)
        return LocationResponse.model_validate(location)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{location_id}", response_model=LocationResponse)
async def update_location(
    location_id: uuid.UUID,
    data: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER]))
):
    """Update location"""
    location = await LocationService.update_location(db=db, location_id=location_id, data=data)
    if not location:
        raise HTTPException(status_code=404, detail="Lokacija ne postoji")
    return LocationResponse.model_validate(location)


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN]))
):
    """Delete location (soft delete)"""
    try:
        success = await LocationService.delete_location(db=db, location_id=location_id)
        if not success:
            raise HTTPException(status_code=404, detail="Lokacija ne postoji")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Article Location Management
# ============================================================================

@router.get("/{location_id}/articles", response_model=List[ArticleInLocationDetail])
async def get_articles_in_location(
    location_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Get all articles in a location"""
    articles = await LocationService.get_articles_in_location(db=db, location_id=location_id)
    return articles


@router.post("/articles", response_model=ArticleLocationResponse, status_code=status.HTTP_201_CREATED)
async def assign_article_to_location(
    data: ArticleLocationCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.MAGACIONER]))
):
    """Assign article to location"""
    try:
        article_loc = await LocationService.assign_article_to_location(db=db, data=data)
        return ArticleLocationResponse.model_validate(article_loc)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# Put-Away (Vođeno skladištenje)
# ============================================================================

@router.post("/putaway/suggest", response_model=PutAwaySuggestResponse)
async def suggest_putaway_location(
    request: PutAwaySuggestRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.MAGACIONER]))
):
    """Get AI-powered location suggestions for put-away"""
    try:
        suggestions = await PutAwayService.suggest_locations(db=db, request=request)
        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/putaway/execute", response_model=PutAwayExecuteResponse)
async def execute_putaway(
    request: PutAwayExecuteRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.MAGACIONER]))
):
    """Execute put-away to selected location"""
    result = await PutAwayService.execute_putaway(db=db, request=request)
    if not result.success:
        raise HTTPException(status_code=400, detail=result.message)
    return result


# ============================================================================
# Pick Route Optimization (Vođeno izdavanje)
# ============================================================================

@router.post("/pick-routes", response_model=PickRouteResponse)
async def generate_pick_route(
    request: PickRouteGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Generate optimized picking route for zaduznica"""
    try:
        route = await PickingService.generate_pick_route(db=db, request=request)
        return route
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/pick-routes/{zaduznica_id}", response_model=PickRouteResponse)
async def get_pick_route(
    zaduznica_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Get existing pick route for zaduznica"""
    route = await PickingService.get_pick_route(db=db, zaduznica_id=zaduznica_id)
    if not route:
        raise HTTPException(status_code=404, detail="Ruta za izdavanje ne postoji")
    return route


# ============================================================================
# Cycle Counting (Popis)
# ============================================================================

@router.get("/cycle-counts", response_model=List[CycleCountSummary])
async def get_cycle_counts(
    status: Optional[str] = None,
    assigned_to_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Get cycle counts with filters"""
    counts = await CycleCountService.get_cycle_counts(
        db=db,
        status=status,
        assigned_to_id=assigned_to_id
    )
    return counts


@router.get("/cycle-counts/{cycle_count_id}", response_model=CycleCountResponse)
async def get_cycle_count_detail(
    cycle_count_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Get cycle count detail with items"""
    count = await CycleCountService.get_cycle_count_detail(db=db, cycle_count_id=cycle_count_id)
    if not count:
        raise HTTPException(status_code=404, detail="Popis ne postoji")
    return count


@router.post("/cycle-counts", response_model=CycleCountResponse, status_code=status.HTTP_201_CREATED)
async def create_cycle_count(
    data: CycleCountCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Create new cycle count task"""
    cycle_count = await CycleCountService.create_cycle_count(db=db, data=data)
    return await CycleCountService.get_cycle_count_detail(db=db, cycle_count_id=cycle_count.id)


@router.post("/cycle-counts/{cycle_count_id}/start", response_model=CycleCountResponse)
async def start_cycle_count(
    cycle_count_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Start cycle count"""
    cycle_count = await CycleCountService.start_cycle_count(
        db=db,
        cycle_count_id=cycle_count_id,
        user_id=user.id
    )
    if not cycle_count:
        raise HTTPException(status_code=404, detail="Popis ne postoji")
    return await CycleCountService.get_cycle_count_detail(db=db, cycle_count_id=cycle_count.id)


@router.post("/cycle-counts/{cycle_count_id}/complete", response_model=CycleCountResponse)
async def complete_cycle_count(
    cycle_count_id: uuid.UUID,
    data: CycleCountComplete,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Complete cycle count with counted quantities"""
    cycle_count = await CycleCountService.complete_cycle_count(
        db=db,
        cycle_count_id=cycle_count_id,
        data=data,
        user_id=user.id
    )
    if not cycle_count:
        raise HTTPException(status_code=404, detail="Popis ne postoji")
    return await CycleCountService.get_cycle_count_detail(db=db, cycle_count_id=cycle_count.id)


@router.post("/cycle-counts/{cycle_count_id}/cancel", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_cycle_count(
    cycle_count_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Cancel cycle count"""
    cycle_count = await CycleCountService.cancel_cycle_count(db=db, cycle_count_id=cycle_count_id)
    if not cycle_count:
        raise HTTPException(status_code=404, detail="Popis ne postoji")


# ============================================================================
# Warehouse Map (Vizualna mapa magacina)
# ============================================================================

@router.get("/warehouse-map", response_model=WarehouseMapResponse)
async def get_warehouse_map(
    magacin_id: uuid.UUID,
    zona: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Get warehouse map data for visualization"""
    from datetime import datetime
    
    # Get all locations with coordinates
    locations = await LocationService.get_locations(
        db=db,
        magacin_id=magacin_id,
        zona=zona,
        is_active=True
    )
    
    # Filter locations with coordinates
    map_locations = [
        {
            "id": loc.id,
            "code": loc.code,
            "naziv": loc.naziv,
            "tip": loc.tip,
            "x": loc.x_coordinate,
            "y": loc.y_coordinate,
            "occupancy_percentage": loc.occupancy_percentage,
            "status_color": loc.status_color,
            "is_active": loc.is_active
        }
        for loc in locations
        if loc.x_coordinate and loc.y_coordinate
    ]
    
    # Get unique zones
    zones = list(set(loc.zona for loc in locations if loc.zona))
    zones.sort()
    
    # Get magacin name
    from ..models.location import Magacin
    from sqlalchemy import select
    query = select(Magacin).where(Magacin.id == magacin_id)
    result = await db.execute(query)
    magacin = result.scalar_one_or_none()
    
    return WarehouseMapResponse(
        magacin_id=magacin_id,
        magacin_naziv=magacin.naziv if magacin else "Nepoznat magacin",
        locations=map_locations,
        zones=zones,
        last_updated=datetime.now()
    )

