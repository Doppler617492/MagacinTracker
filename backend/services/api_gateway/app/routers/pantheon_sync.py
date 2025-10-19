"""
Pantheon Sync API Routes
Admin-only endpoints to trigger Pantheon ERP synchronization
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from httpx import AsyncClient
from pydantic import BaseModel

from app_common.logging import get_logger
from ..services.auth import require_roles
from ..dependencies.http import get_task_client

logger = get_logger(__name__)
router = APIRouter()


# =========================================================================
# REQUEST/RESPONSE MODELS
# =========================================================================

class SyncResponse(BaseModel):
    """Standard sync response"""
    status: str
    total_fetched: int = 0
    created: int = 0
    updated: int = 0
    errors: int = 0
    duration_seconds: float = 0
    message: str = ""


# =========================================================================
# SYNC ENDPOINTS (ADMIN ONLY)
# =========================================================================

@router.post("/sync/catalog", response_model=SyncResponse)
async def trigger_catalog_sync(
    request: Request,
    full_sync: bool = Query(False, description="If true, sync all articles; if false, delta sync"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN"]))
):
    """
    Trigger Pantheon catalog (articles) synchronization
    
    - **ADMIN ONLY**
    - Delta sync by default (only changed articles)
    - Use full_sync=true for complete catalog refresh
    """
    try:
        logger.info(f"📊 Catalog sync triggered by {user.get('email')} (full_sync={full_sync})")
        
        from ..dependencies.http import build_forward_headers
        headers = build_forward_headers(request, user)
        
        response = await task_client.post(
            "/api/pantheon/sync/catalog",
            json={"full_sync": full_sync},
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        
        return SyncResponse(
            status="success",
            total_fetched=data.get("total_fetched", 0),
            created=data.get("articles_created", 0),
            updated=data.get("articles_updated", 0),
            errors=data.get("errors", 0),
            duration_seconds=data.get("duration", 0),
            message=f"Catalog sync completed: {data.get('articles_created', 0)} created, {data.get('articles_updated', 0)} updated"
        )
        
    except Exception as e:
        logger.error(f"Catalog sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/subjects", response_model=SyncResponse)
async def trigger_subjects_sync(
    request: Request,
    full_sync: bool = Query(False),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN"]))
):
    """
    Trigger Pantheon subjects/partners synchronization
    
    - **ADMIN ONLY**
    - Syncs suppliers, customers, warehouses
    """
    try:
        logger.info(f"👥 Subjects sync triggered by {user.get('email')} (full_sync={full_sync})")
        
        from ..dependencies.http import build_forward_headers
        headers = build_forward_headers(request, user)
        
        response = await task_client.post(
            "/api/pantheon/sync/subjects",
            json={"full_sync": full_sync},
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        
        return SyncResponse(
            status="success",
            total_fetched=data.get("total_fetched", 0),
            created=data.get("subjects_created", 0),
            updated=data.get("subjects_updated", 0),
            errors=data.get("errors", 0),
            duration_seconds=data.get("duration", 0),
            message=f"Subjects sync completed: {data.get('subjects_created', 0)} created"
        )
        
    except Exception as e:
        logger.error(f"Subjects sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/dispatches", response_model=SyncResponse)
async def trigger_dispatch_sync(
    request: Request,
    date_from: Optional[date] = Query(None, description="Start date (default: last 2 hours)"),
    date_to: Optional[date] = Query(None, description="End date (default: now)"),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN", "MENADZER"]))
):
    """
    Trigger Pantheon outbound/issue documents synchronization
    
    - **ADMIN/MENADZER ONLY**
    - Imports outbound documents with exists_in_wms logic
    - Only items with exists_in_wms=true create WMS tasks
    """
    try:
        logger.info(f"📤 Dispatch sync triggered by {user.get('email')} ({date_from} to {date_to})")
        
        from ..dependencies.http import build_forward_headers
        headers = build_forward_headers(request, user)
        
        params = {}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        response = await task_client.post(
            "/api/pantheon/sync/dispatches",
            json=params,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        
        return SyncResponse(
            status="success",
            total_fetched=data.get("total_docs", 0),
            created=data.get("docs_created", 0),
            updated=data.get("docs_updated", 0),
            errors=data.get("errors", 0),
            duration_seconds=data.get("duration", 0),
            message=f"Dispatch sync completed: {data.get('items_exists_in_wms', 0)} WMS-eligible items"
        )
        
    except Exception as e:
        logger.error(f"Dispatch sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/receipts", response_model=SyncResponse)
async def trigger_receipt_sync(
    request: Request,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN", "MENADZER"]))
):
    """
    Trigger Pantheon inbound/receipt documents synchronization
    
    - **ADMIN/MENADZER ONLY**
    """
    try:
        logger.info(f"📥 Receipt sync triggered by {user.get('email')} ({date_from} to {date_to})")
        
        from ..dependencies.http import build_forward_headers
        headers = build_forward_headers(request, user)
        
        params = {}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        response = await task_client.post(
            "/api/pantheon/sync/receipts",
            json=params,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        data = response.json()
        
        return SyncResponse(
            status="success",
            total_fetched=data.get("total_docs", 0),
            created=data.get("docs_created", 0),
            updated=data.get("docs_updated", 0),
            errors=data.get("errors", 0),
            duration_seconds=data.get("duration", 0),
            message=f"Receipt sync completed: {data.get('total_items', 0)} items"
        )
        
    except Exception as e:
        logger.error(f"Receipt sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =========================================================================
# DATA QUERY ENDPOINTS
# =========================================================================

@router.get("/dispatches")
async def list_dispatches(
    request: Request,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    doc_type: Optional[str] = Query(None),
    only_wms: bool = Query(False, description="Only show items with exists_in_wms=true"),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN", "MENADZER", "SEF"]))
):
    """
    List outbound/dispatch documents
    
    - Filter by date range, doc type, WMS eligibility
    - Pagination supported
    """
    try:
        params = {
            "limit": limit,
            "offset": offset,
            "only_wms": only_wms
        }
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        if doc_type:
            params["doc_type"] = doc_type
        
        response = await task_client.get(
            "/api/pantheon/dispatches",
            params=params,
            headers={"Authorization": request.headers.get("Authorization")}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to list dispatches: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispatches/{dispatch_id}")
async def get_dispatch(
    dispatch_id: str,
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN", "MENADZER", "SEF"]))
):
    """Get dispatch document details"""
    try:
        response = await task_client.get(
            f"/api/pantheon/dispatches/{dispatch_id}",
            headers={"Authorization": request.headers.get("Authorization")}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to get dispatch {dispatch_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/receipts")
async def list_receipts(
    request: Request,
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(50, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN", "MENADZER", "SEF"]))
):
    """List inbound/receipt documents"""
    try:
        params = {"limit": limit, "offset": offset}
        if date_from:
            params["date_from"] = date_from.isoformat()
        if date_to:
            params["date_to"] = date_to.isoformat()
        
        response = await task_client.get(
            "/api/pantheon/receipts",
            params=params,
            headers={"Authorization": request.headers.get("Authorization")}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to list receipts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subjects")
async def list_subjects(
    request: Request,
    type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    task_client: AsyncClient = Depends(get_task_client),
    user: dict = Depends(require_roles(["ADMIN", "MENADZER", "SEF"]))
):
    """List subjects/partners from Pantheon"""
    try:
        params = {"limit": limit, "offset": offset}
        if type:
            params["type"] = type
        
        from ..dependencies.http import build_forward_headers
        headers = build_forward_headers(request, user)
        
        response = await task_client.get(
            "/api/pantheon/subjects",
            params=params,
            headers=headers
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()
        
    except Exception as e:
        logger.error(f"Failed to list subjects: {e}")
        raise HTTPException(status_code=500, detail=str(e))

