from __future__ import annotations

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..dependencies import get_task_client
from ..dependencies.http import build_forward_headers
from ..services.auth import get_current_user

router = APIRouter()


@router.get("/trebovanja", response_model=dict)
async def list_trebovanja(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    magacin_id: Optional[UUID] = None,
    radnja_id: Optional[UUID] = None,
    search: Optional[str] = None,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    params = {
        "page": page,
        "page_size": page_size,
    }
    if status_filter:
        params["status"] = status_filter
    if magacin_id:
        params["magacin_id"] = str(magacin_id)
    if radnja_id:
        params["radnja_id"] = str(radnja_id)
    if search:
        params["search"] = search

    response = await client.get(
        "/api/trebovanja",
        params=params,
        headers=build_forward_headers(request, user),
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/trebovanja/{trebovanje_id}", response_model=dict)
async def get_trebovanje(
    trebovanje_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.get(
        f"/api/trebovanja/{trebovanje_id}",
        headers=build_forward_headers(request, user),
    )
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trebovanje not found")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/trebovanja/import", response_model=dict, status_code=status.HTTP_201_CREATED)
async def import_trebovanje(
    payload: dict,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.post(
        "/api/trebovanja/import",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
