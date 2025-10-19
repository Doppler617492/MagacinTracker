"""
Stream events and metrics router - proxies to task service.
"""
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, status
from httpx import AsyncClient

from app_common.logging import get_logger
from ..dependencies.http import get_task_client
from ..services.auth import require_roles

logger = get_logger(__name__)
router = APIRouter()


def _forward_headers(request: Request) -> dict:
    """Extract and forward necessary headers"""
    headers = {}
    auth_header = request.headers.get("Authorization")
    if auth_header:
        headers["Authorization"] = auth_header
    return headers


@router.get("/stream/events/recent")
async def get_recent_events(
    request: Request,
    limit: int = 100,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get recent system events."""
    response = await task_client.get(
        f"/api/stream/events/recent?limit={limit}",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/stream/events/worker-activity")
async def get_worker_activity(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get current worker activity metrics."""
    response = await task_client.get(
        "/api/stream/events/worker-activity",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/stream/events/warehouse-load")
async def get_warehouse_load(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get current warehouse load metrics."""
    response = await task_client.get(
        "/api/stream/events/warehouse-load",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/stream/metrics")
async def get_stream_metrics(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get stream processing metrics."""
    response = await task_client.get(
        "/api/stream/metrics",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/stream/metrics/throughput")
async def get_throughput_metrics(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get throughput metrics."""
    response = await task_client.get(
        "/api/stream/metrics/throughput",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/stream/metrics/performance")
async def get_performance_metrics(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get performance metrics."""
    response = await task_client.get(
        "/api/stream/metrics/performance",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/stream/metrics/health")
async def get_health_metrics(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get health metrics."""
    response = await task_client.get(
        "/api/stream/metrics/health",
        headers=_forward_headers(request)
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()

