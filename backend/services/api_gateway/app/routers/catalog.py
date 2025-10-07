from __future__ import annotations

from typing import Optional
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..dependencies import build_forward_headers, get_catalog_client, get_task_client
from ..services.auth import get_current_user

router = APIRouter()

_ALLOWED_LIST_ROLES = {"menadzer", "sef", "komercijalista"}
_ALLOWED_EDIT_ROLES = {"menadzer", "sef"}


def _enforce_roles(user: dict, allowed: set[str]) -> None:
    roles = set(user.get("roles") or [])
    if user.get("role"):
        roles.add(str(user["role"]))
    if roles.isdisjoint(allowed):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")


@router.get("/catalog/articles", response_model=dict)
async def list_catalog_articles(
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
    search: Optional[str] = Query(default=None, min_length=1),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=25, ge=1, le=100),
) -> dict:
    _enforce_roles(user, _ALLOWED_LIST_ROLES)
    params = {"page": page, "size": size}
    if search:
        params["search"] = search

    response = await client.get(
        "/api/catalog/articles",
        params=params,
        headers=build_forward_headers(request, user),
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.patch("/catalog/articles/{article_id}", response_model=dict)
async def update_catalog_article(
    article_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    _enforce_roles(user, _ALLOWED_EDIT_ROLES)
    response = await client.patch(
        f"/api/catalog/articles/{article_id}",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 202):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


# FastAPI handles Optional payload gracefully; use None default to avoid mutable default warning.
@router.post("/catalog/sync", response_model=dict)
async def trigger_catalog_sync(
    request: Request,
    payload: dict | None = None,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_catalog_client),
) -> dict:
    _enforce_roles(user, _ALLOWED_EDIT_ROLES)
    response = await client.post(
        "/api/catalog/sync",
        json=payload or {},
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 202):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/catalog/status", response_model=dict)
async def catalog_sync_status(
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_catalog_client),
) -> dict:
    _enforce_roles(user, _ALLOWED_EDIT_ROLES)
    response = await client.get(
        "/api/catalog/status",
        headers=build_forward_headers(request, user),
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
