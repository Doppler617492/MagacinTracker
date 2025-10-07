from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from ..dependencies import build_forward_headers, get_task_client
from ..services.auth import get_current_user

router = APIRouter()


@router.get("/tv/snapshot", response_model=dict)
async def tv_snapshot(
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.get(
        "/api/tv/snapshot",
        headers=build_forward_headers(request, user),
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
