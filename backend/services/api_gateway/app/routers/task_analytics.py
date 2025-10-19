from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request
from httpx import AsyncClient

from ..services.auth import get_current_user
from ..dependencies.http import build_forward_headers, get_task_client

router = APIRouter()


@router.get("/tasks/summary")
async def get_task_summary(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get task completion summary."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/tasks/summary", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.get("/tasks/worker-performance")
async def get_worker_performance(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get worker performance data."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/tasks/worker-performance", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.get("/tasks/completion-trends")
async def get_completion_trends(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> List[Dict[str, Any]]:
    """Get task completion trends over time."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/tasks/completion-trends", params=params, headers=headers)
    response.raise_for_status()
    return response.json()


@router.get("/tasks/detailed-stats")
async def get_detailed_stats(
    request: Request,
    radnja_id: Optional[uuid.UUID] = Query(None, description="Filter by radnja ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get detailed task statistics."""
    params = {"days": days}
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    
    headers = build_forward_headers(request, user)
    response = await task_client.get("/api/tasks/detailed-stats", params=params, headers=headers)
    response.raise_for_status()
    return response.json()
