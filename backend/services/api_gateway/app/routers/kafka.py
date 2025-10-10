from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from httpx import AsyncClient

from app_common.logging import get_logger
from ..dependencies.http import get_task_service_client
from ..services.auth import require_roles

logger = get_logger(__name__)
router = APIRouter()


@router.get("/kafka/metrics")
async def get_kafka_metrics(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Kafka streaming metrics."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/kafka/metrics", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("KAFKA_METRICS_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Kafka metrics"
        )


@router.get("/kafka/analytics")
async def get_kafka_analytics(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Kafka analytics data."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/kafka/analytics", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("KAFKA_ANALYTICS_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Kafka analytics"
        )


@router.get("/kafka/performance")
async def get_kafka_performance(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Kafka performance metrics."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/kafka/performance", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("KAFKA_PERFORMANCE_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Kafka performance"
        )


@router.post("/kafka/events/publish")
async def publish_kafka_event(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to publish Kafka event."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {"content-type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
            
        body = await request.body()
        response = await task_client.post("/api/kafka/events/publish", content=body, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("KAFKA_PUBLISH_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish Kafka event"
        )

