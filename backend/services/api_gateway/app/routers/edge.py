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

