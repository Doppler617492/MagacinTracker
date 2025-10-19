"""
AI Intelligence Layer API endpoints
Manhattan Active WMS - Phase 4
"""
import uuid
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, require_role
from ..models.enums import Role
from ..schemas.ai_schemas import (
    BinSuggestionRequest,
    BinSuggestionResponse,
    BinAcceptRequest,
    BinRejectRequest,
    RestockSuggestionRequest,
    RestockSuggestionResponse,
    RestockApproveRequest,
    RestockRejectRequest,
    AnomalyListItem,
    AnomalyDetailResponse,
    AnomalyAckRequest,
    AnomalyResolveRequest,
    ShiftSummaryResponse,
    TeamComparisonResponse,
    BinHeatmapResponse,
)
from ..services.ai_bin_allocation import AIBinAllocationService
from ..services.ai_restocking import AIRestockingService
from ..services.ai_anomaly_detection import AIAnomalyDetectionService
from ...app_common.feature_flags import (
    is_ai_bin_allocation_enabled,
    is_ai_restocking_enabled,
    is_ai_anomaly_enabled,
    is_smart_kpi_enabled,
)

router = APIRouter(prefix="/ai", tags=["AI Intelligence"])


# ============================================================================
# AI Bin Allocation Endpoints
# ============================================================================

@router.post("/bin-suggest", response_model=BinSuggestionResponse)
async def suggest_bin_locations(
    request: BinSuggestionRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """
    Get AI-powered bin suggestions for receiving item
    
    Requires: FF_AI_BIN_ALLOCATION=true
    """
    if not is_ai_bin_allocation_enabled():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AI Bin Allocation nije omogućen"
        )
    
    try:
        suggestions = await AIBinAllocationService.suggest_bins(
            db=db,
            receiving_item_id=request.receiving_item_id,
            artikal_id=request.artikal_id,
            quantity=request.quantity,
            magacin_id=request.magacin_id
        )
        
        return BinSuggestionResponse(
            suggestions=suggestions,
            model_version=AIBinAllocationService.MODEL_VERSION,
            latency_ms=suggestions[0]['latency_ms'] if suggestions else 0
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/bin-accept", status_code=status.HTTP_200_OK)
async def accept_bin_suggestion(
    request: BinAcceptRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Accept AI bin suggestion and execute put-away"""
    if not is_ai_bin_allocation_enabled():
        raise HTTPException(status_code=404, detail="AI Bin Allocation nije omogućen")
    
    success = await AIBinAllocationService.accept_suggestion(
        db=db,
        receiving_item_id=request.receiving_item_id,
        location_id=request.location_id,
        user_id=user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Predlog nije pronađen")
    
    return {"message": "Predlog prihvaćen"}


@router.post("/bin-reject", status_code=status.HTTP_200_OK)
async def reject_bin_suggestion(
    request: BinRejectRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF, Role.MAGACIONER]))
):
    """Reject AI bin suggestion"""
    if not is_ai_bin_allocation_enabled():
        raise HTTPException(status_code=404, detail="AI Bin Allocation nije omogućen")
    
    success = await AIBinAllocationService.reject_suggestion(
        db=db,
        receiving_item_id=request.receiving_item_id,
        user_id=user.id,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Predlog nije pronađen")
    
    return {"message": "Predlog odbijen"}


# ============================================================================
# AI Restocking Endpoints
# ============================================================================

@router.post("/restock/suggest", response_model=RestockSuggestionResponse)
async def suggest_restocking(
    request: RestockSuggestionRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """
    Generate AI restocking suggestions
    
    Requires: FF_AI_RESTOCKING=true
    """
    if not is_ai_restocking_enabled():
        raise HTTPException(status_code=404, detail="AI Restocking nije omogućen")
    
    suggestions = await AIRestockingService.generate_suggestions(
        db=db,
        magacin_id=request.magacin_id,
        horizon_days=request.horizon_days
    )
    
    return RestockSuggestionResponse(
        suggestions=suggestions,
        total_count=len(suggestions),
        model_version=AIRestockingService.MODEL_VERSION
    )


@router.post("/restock/approve", status_code=status.HTTP_200_OK)
async def approve_restocking(
    request: RestockApproveRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Approve restocking suggestions (creates internal trebovanje)"""
    if not is_ai_restocking_enabled():
        raise HTTPException(status_code=404, detail="AI Restocking nije omogućen")
    
    trebovanje_ids = []
    for suggestion_id in request.suggestion_ids:
        trebovanje_id = await AIRestockingService.approve_suggestion(
            db=db,
            suggestion_id=suggestion_id,
            user_id=user.id
        )
        if trebovanje_id:
            trebovanje_ids.append(str(trebovanje_id))
    
    return {
        "message": f"{len(trebovanje_ids)} predloga odobreno",
        "trebovanje_ids": trebovanje_ids
    }


@router.post("/restock/reject", status_code=status.HTTP_200_OK)
async def reject_restocking(
    request: RestockRejectRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Reject restocking suggestion"""
    if not is_ai_restocking_enabled():
        raise HTTPException(status_code=404, detail="AI Restocking nije omogućen")
    
    success = await AIRestockingService.reject_suggestion(
        db=db,
        suggestion_id=request.suggestion_id,
        user_id=user.id,
        reason=request.reason
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Predlog nije pronađen")
    
    return {"message": "Predlog odbijen"}


# ============================================================================
# AI Anomaly Detection Endpoints
# ============================================================================

@router.get("/anomalies", response_model=List[AnomalyListItem])
async def get_anomalies(
    type: Optional[str] = None,
    status: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """
    Get anomalies with filters
    
    Requires: FF_AI_ANOMALY=true
    """
    if not is_ai_anomaly_enabled():
        raise HTTPException(status_code=404, detail="AI Anomaly nije omogućen")
    
    from ..models.ai_models import AIAnomaly
    
    query = select(AIAnomaly)
    
    filters = []
    if type:
        filters.append(AIAnomaly.type == type)
    if status:
        filters.append(AIAnomaly.status == status)
    if from_date:
        filters.append(AIAnomaly.detected_at >= from_date)
    if to_date:
        filters.append(AIAnomaly.detected_at <= to_date)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(AIAnomaly.detected_at.desc())
    
    result = await db.execute(query)
    anomalies = result.scalars().all()
    
    return [AnomalyListItem.model_validate(a) for a in anomalies]


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyDetailResponse)
async def get_anomaly_detail(
    anomaly_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Get anomaly details"""
    if not is_ai_anomaly_enabled():
        raise HTTPException(status_code=404, detail="AI Anomaly nije omogućen")
    
    from ..models.ai_models import AIAnomaly
    anomaly = await db.get(AIAnomaly, anomaly_id)
    
    if not anomaly:
        raise HTTPException(status_code=404, detail="Anomalija nije pronađena")
    
    return AnomalyDetailResponse.model_validate(anomaly)


@router.post("/anomalies/{anomaly_id}/ack", status_code=status.HTTP_200_OK)
async def acknowledge_anomaly(
    anomaly_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Acknowledge anomaly (mark as "u obradi")"""
    if not is_ai_anomaly_enabled():
        raise HTTPException(status_code=404, detail="AI Anomaly nije omogućen")
    
    success = await AIAnomalyDetectionService.acknowledge_anomaly(
        db=db,
        anomaly_id=anomaly_id,
        user_id=user.id
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Anomalija nije pronađena")
    
    return {"message": "Anomalija primljena na znanje"}


@router.post("/anomalies/{anomaly_id}/resolve", status_code=status.HTTP_200_OK)
async def resolve_anomaly(
    anomaly_id: uuid.UUID,
    request: AnomalyResolveRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """Resolve anomaly with resolution note"""
    if not is_ai_anomaly_enabled():
        raise HTTPException(status_code=404, detail="AI Anomaly nije omogućen")
    
    success = await AIAnomalyDetectionService.resolve_anomaly(
        db=db,
        anomaly_id=anomaly_id,
        user_id=user.id,
        resolution_note=request.resolution_note
    )
    
    if not success:
        raise HTTPException(status_code=404, detail="Anomalija nije pronađena")
    
    return {"message": "Anomalija rešena"}


# ============================================================================
# Smart KPI Endpoints (Simplified)
# ============================================================================

@router.get("/kpi/shift-summary", response_model=List[ShiftSummaryResponse])
async def get_shift_summary(
    date: Optional[str] = None,  # YYYY-MM-DD
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """
    Get shift summary (Smena A 08-15, Smena B 12-19)
    
    Requires: FF_SMART_KPI=true
    """
    if not is_smart_kpi_enabled():
        raise HTTPException(status_code=404, detail="Smart KPI nije omogućen")
    
    # Parse date
    target_date = datetime.strptime(date, '%Y-%m-%d').date() if date else datetime.now().date()
    
    # Define shifts
    shifts = [
        {'name': 'Smena A (08-15)', 'start_hour': 8, 'end_hour': 15},
        {'name': 'Smena B (12-19)', 'start_hour': 12, 'end_hour': 19},
    ]
    
    from ..models.zaduznica import ZaduznicaStavka
    
    results = []
    for shift in shifts:
        shift_start = datetime.combine(target_date, datetime.min.time()).replace(hour=shift['start_hour'], tzinfo=timezone.utc)
        shift_end = datetime.combine(target_date, datetime.min.time()).replace(hour=shift['end_hour'], tzinfo=timezone.utc)
        
        # Query tasks completed in shift
        query = select(
            func.count(ZaduznicaStavka.id).label('total'),
            func.sum(func.case((ZaduznicaStavka.is_partial == True, 1), else_=0)).label('partial'),
            func.avg(ZaduznicaStavka.duration_seconds).label('avg_duration')
        ).where(
            and_(
                ZaduznicaStavka.completed_at >= shift_start,
                ZaduznicaStavka.completed_at < shift_end,
                ZaduznicaStavka.status == 'done'
            )
        )
        result = await db.execute(query)
        stats = result.one()
        
        picks_per_hour = stats.total / 7.0 if stats.total > 0 else 0.0  # 7-hour shift
        accuracy = ((stats.total - stats.partial) / stats.total * 100) if stats.total > 0 else 100.0
        
        results.append(ShiftSummaryResponse(
            shift_name=shift['name'],
            date=str(target_date),
            tasks_completed=stats.total or 0,
            tasks_partial=stats.partial or 0,
            avg_completion_time_minutes=(stats.avg_duration / 60.0) if stats.avg_duration else 0.0,
            picks_per_hour=picks_per_hour,
            accuracy_percentage=accuracy,
            workers_count=0  # Placeholder
        ))
    
    return results


@router.get("/kpi/bin-heatmap", response_model=BinHeatmapResponse)
async def get_bin_heatmap(
    zona: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_role([Role.ADMIN, Role.MENADZER, Role.SEF]))
):
    """
    Get bin heatmap (occupancy, turnover, problem score)
    
    Requires: FF_SMART_KPI=true
    """
    if not is_smart_kpi_enabled():
        raise HTTPException(status_code=404, detail="Smart KPI nije omogućen")
    
    from ..models.locations import Location
    from ..models.enums import LocationType
    
    # Get bins
    query = select(Location).where(
        and_(
            Location.tip == LocationType.BIN,
            Location.is_active == True
        )
    )
    
    if zona:
        query = query.where(Location.zona == zona)
    
    result = await db.execute(query)
    bins = result.scalars().all()
    
    heatmap_items = []
    for bin_loc in bins:
        # Calculate problem score (high occupancy + low turnover = problem)
        occupancy = bin_loc.occupancy_percentage
        problem_score = occupancy if occupancy > 80 else 0.0
        
        heatmap_items.append({
            'location_id': str(bin_loc.id),
            'location_code': bin_loc.code,
            'occupancy_percentage': occupancy,
            'turnover_rate': 0.0,  # Placeholder
            'avg_pick_time_seconds': 0.0,  # Placeholder
            'problem_score': problem_score
        })
    
    return BinHeatmapResponse(
        bins=heatmap_items,
        zona=zona,
        total_count=len(heatmap_items)
    )

