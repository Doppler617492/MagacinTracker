from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from ..dependencies.auth import require_roles
from ..models.enums import Role

from ..schemas.kpi import (
    CSVExportRequest,
    CSVExportResponse,
    DailyStatsResponse,
    KPIFilters,
    KPISummaryResponse,
    ManualCompletionStatsResponse,
    TopWorkerResponse,
)
from ..services.kpi import KPIService

router = APIRouter()


@router.get("/summary", response_model=KPISummaryResponse)
async def get_kpi_summary(
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_roles([Role.SEF, Role.MENADZER])),
) -> KPISummaryResponse:
    """Get KPI summary with filtering options."""
    kpi_service = KPIService(session)
    result = await kpi_service.get_summary(radnja_id, radnik_id, days)
    return KPISummaryResponse(**result)


@router.get("/daily-stats", response_model=List[DailyStatsResponse])
async def get_daily_stats(
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_roles([Role.SEF, Role.MENADZER])),
) -> List[DailyStatsResponse]:
    """Get daily statistics for the specified period."""
    kpi_service = KPIService(session)
    result = await kpi_service.get_daily_stats(radnja_id, radnik_id, days)
    return [DailyStatsResponse(**item) for item in result]


@router.get("/top-workers", response_model=List[TopWorkerResponse])
async def get_top_workers(
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(5, ge=1, le=50, description="Number of top workers to return"),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_roles([Role.SEF, Role.MENADZER])),
) -> List[TopWorkerResponse]:
    """Get top performing workers by task completion."""
    kpi_service = KPIService(session)
    result = await kpi_service.get_top_workers(radnja_id, days, limit)
    return [TopWorkerResponse(**item) for item in result]


@router.get("/manual-completion", response_model=ManualCompletionStatsResponse)
async def get_manual_completion_stats(
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_roles([Role.SEF, Role.MENADZER])),
) -> ManualCompletionStatsResponse:
    """Get manual completion statistics."""
    kpi_service = KPIService(session)
    result = await kpi_service.get_manual_completion_stats(radnja_id, radnik_id, days)
    return ManualCompletionStatsResponse(**result)


@router.post("/export", response_model=CSVExportResponse)
async def export_kpi_data(
    request: CSVExportRequest,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(require_roles([Role.SEF, Role.MENADZER])),
) -> CSVExportResponse:
    """Export KPI data to CSV format."""
    # This will be implemented in the next phase
    # For now, return a placeholder response
    return CSVExportResponse(
        filename="kpi_export_placeholder.csv",
        download_url="/api/kpi/download/placeholder",
        record_count=0,
        generated_at=datetime.utcnow()
    )
