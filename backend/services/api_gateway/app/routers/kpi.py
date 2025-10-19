from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from httpx import AsyncClient

from app_common.logging import get_logger
from ..dependencies.http import build_forward_headers, get_task_client
from ..services.auth import get_current_user, require_roles

logger = get_logger(__name__)
router = APIRouter()


@router.get("/summary")
async def get_kpi_summary(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    days: int = Query(7, ge=1, le=365, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get KPI summary with filtering options."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    if radnik_id:
        params["radnik_id"] = str(radnik_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/kpi/summary", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.get("/daily-stats")
async def get_daily_stats(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get daily statistics for the specified period."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    if radnik_id:
        params["radnik_id"] = str(radnik_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/kpi/daily-stats", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.get("/top-workers")
async def get_top_workers(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(5, ge=1, le=50, description="Number of top workers to return"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get top performing workers by task completion."""
    params = {"days": days, "limit": limit}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/kpi/top-workers", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.get("/manual-completion")
async def get_manual_completion_stats(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get manual completion statistics."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    if radnik_id:
        params["radnik_id"] = str(radnik_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/kpi/manual-completion", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.post("/export")
async def export_kpi_data(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["admin", "sef", "menadzer"])),
) -> Dict[str, Any]:
    """Export KPI data to CSV format."""
    # Forward the request body to task service
    body = await request.body()
    response = await task_client.post(
        "/api/kpi/export",
        content=body,
        headers={"content-type": "application/json"}
    )
    response.raise_for_status()
    return response.json()


@router.get("/predict")
async def get_kpi_forecast(
    request: Request,
    metric: str = Query("items_completed", description="Metric to forecast"),
    period: int = Query(90, ge=7, le=365, description="Historical period in days"),
    horizon: int = Query(7, ge=1, le=30, description="Forecast horizon in days"),
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    radnik_id: Optional[uuid.UUID] = Query(None, description="Filter by radnik ID"),
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["sef", "menadzer", "magacioner"])),
) -> Dict[str, Any]:
    """Get KPI forecast with confidence intervals and anomaly detection."""
    start_time = datetime.utcnow()
    
    try:
        # Prepare parameters
        params = {
            "metric": metric,
            "period": period,
            "horizon": horizon
        }
        if radnja_id:
            params["radnja_id"] = str(radnja_id)
        if radnik_id:
            params["radnik_id"] = str(radnik_id)
        
        # Forward the Authorization header from the original request
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
        
        # Get forecast from task service
        response = await task_client.get("/api/kpi/predict", params=params, headers=headers)
        response.raise_for_status()
        forecast_data = response.json()
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Log forecast generation
        logger.info(
            "FORECAST_GENERATED",
            metric=metric,
            period=period,
            horizon=horizon,
            processing_time_ms=processing_time,
            confidence=forecast_data.get("confidence", 0),
            anomaly_detected=forecast_data.get("anomaly_detected", False),
            user_id=getattr(request.state, "user_id", "unknown")
        )
        
        return forecast_data
        
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error(
            "FORECAST_ERROR",
            metric=metric,
            period=period,
            horizon=horizon,
            error=str(e),
            processing_time_ms=processing_time,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        raise HTTPException(status_code=500, detail=f"Greška pri generisanju prognoze: {str(e)}")
