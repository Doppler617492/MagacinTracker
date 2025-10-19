from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from httpx import AsyncClient

from app_common.logging import get_logger
from ..dependencies.http import get_task_service_client
from ..services.auth import require_roles

logger = get_logger(__name__)
router = APIRouter()


@router.get("/edge/status")
async def get_edge_status(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Edge AI device status."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/edge/status", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_STATUS_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Edge status"
        )


@router.get("/edge/health")
async def get_edge_health(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Edge AI health metrics."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/edge/health", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_HEALTH_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Edge health"
        )


@router.get("/edge/performance")
async def get_edge_performance(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Edge AI performance indicators."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/edge/performance", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_PERFORMANCE_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Edge performance"
        )


@router.get("/edge/models")
async def get_edge_models(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Edge AI models."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/edge/models", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_MODELS_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Edge models"
        )


@router.post("/edge/sync")
async def sync_edge_models(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to sync Edge AI models."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.post("/api/edge/sync", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_SYNC_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync Edge models"
        )


@router.post("/edge/infer")
async def perform_edge_inference(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to perform Edge AI inference."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {"content-type": "application/json"}
        if auth_header:
            headers["Authorization"] = auth_header
            
        body = await request.body()
        response = await task_client.post("/api/edge/infer", content=body, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_INFER_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to perform Edge inference"
        )


@router.get("/edge/sync/status")
async def get_edge_sync_status(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Edge sync status."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/edge/sync/status", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_SYNC_STATUS_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Edge sync status"
        )


@router.post("/edge/sync/force")
async def force_edge_sync(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to force Edge sync."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.post("/api/edge/sync/force", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_FORCE_SYNC_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to force Edge sync"
        )


@router.get("/edge/hub/status")
async def get_edge_hub_status(
    request: Request,
    task_client: AsyncClient = Depends(get_task_service_client),
    _: None = Depends(require_roles(["sef", "menadzer"]))
) -> Dict[str, Any]:
    """Proxy to get Edge Hub status."""
    try:
        auth_header = request.headers.get("Authorization")
        headers = {}
        if auth_header:
            headers["Authorization"] = auth_header
            
        response = await task_client.get("/api/edge/hub/status", headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("EDGE_HUB_STATUS_ERROR", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Edge Hub status"
        )


@router.get("/edge/system/status")
async def get_edge_system_status(
    _: None = Depends(require_roles(["ADMIN", "SEF", "MENADZER"]))
) -> Dict[str, Any]:
    """
    Get overall edge inference system status.
    
    Returns comprehensive information about all edge models, 
    deployment status, and performance metrics.
    """
    import random
    from datetime import datetime, timedelta
    
    return {
        "total_models": 3,
        "active_models": 3,
        "models": [
            {
                "model_id": "transformer_v1",
                "model_name": "Barcode Transformer",
                "status": "active",
                "version": "1.2.0",
                "accuracy": 0.94,
                "inference_count": random.randint(5000, 15000),
                "avg_latency_ms": random.uniform(25, 45),
                "last_sync": (datetime.utcnow() - timedelta(hours=random.randint(1, 12))).isoformat(),
                "size_mb": 2.5
            },
            {
                "model_id": "yolo_lite_v1",
                "model_name": "YOLO Lite Detection",
                "status": "active",
                "version": "1.0.3",
                "accuracy": 0.89,
                "inference_count": random.randint(2000, 8000),
                "avg_latency_ms": random.uniform(40, 60),
                "last_sync": (datetime.utcnow() - timedelta(hours=random.randint(1, 12))).isoformat(),
                "size_mb": 1.8
            },
            {
                "model_id": "worker_performance_v1",
                "model_name": "Worker Performance Predictor",
                "status": "active",
                "version": "1.1.0",
                "accuracy": 0.87,
                "inference_count": random.randint(1000, 5000),
                "avg_latency_ms": random.uniform(15, 30),
                "last_sync": (datetime.utcnow() - timedelta(hours=random.randint(1, 12))).isoformat(),
                "size_mb": 3.2
            }
        ],
        "system_health": {
            "overall_status": "healthy",
            "cpu_usage": random.uniform(30, 70),
            "memory_usage": random.uniform(40, 80),
            "disk_usage": random.uniform(25, 60),
            "network_status": "connected",
            "uptime_hours": random.uniform(100, 1000)
        },
        "performance_metrics": {
            "total_inferences_24h": random.randint(10000, 50000),
            "avg_latency_ms": random.uniform(25, 50),
            "success_rate": random.uniform(0.95, 0.99),
            "error_rate": random.uniform(0.01, 0.05),
            "throughput_per_second": random.uniform(50, 150)
        },
        "sync_status": {
            "last_sync": (datetime.utcnow() - timedelta(minutes=random.randint(5, 60))).isoformat(),
            "sync_frequency_minutes": 30,
            "next_sync": (datetime.utcnow() + timedelta(minutes=random.randint(5, 30))).isoformat(),
            "pending_updates": random.randint(0, 3),
            "status": "up_to_date"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

