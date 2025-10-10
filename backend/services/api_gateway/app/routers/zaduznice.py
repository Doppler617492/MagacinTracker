from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ..dependencies import build_forward_headers, get_task_client
from ..services.auth import get_current_user

router = APIRouter()


@router.post("/zaduznice", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_zaduznice(
    payload: dict,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.post(
        "/api/zaduznice",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post(
    "/zaduznice/predlog/{trebovanje_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def cancel_scheduler_suggestion(
    trebovanje_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> Response:
    response = await client.post(
        f"/api/zaduznice/predlog/{trebovanje_id}/cancel",
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return Response(status_code=response.status_code)


@router.patch("/zaduznice/{zaduznica_id}/status", status_code=status.HTTP_200_OK)
async def update_zaduznica_status(
    zaduznica_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> None:
    response = await client.patch(
        f"/api/zaduznice/{zaduznica_id}/status",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return


@router.post("/zaduznice/{zaduznica_id}/reassign", status_code=status.HTTP_200_OK)
async def reassign_zaduznica(
    zaduznica_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> None:
    response = await client.post(
        f"/api/zaduznice/{zaduznica_id}/reassign",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 204):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return


@router.get("/zaduznice/{zaduznica_id}", response_model=dict)
async def zaduznica_detail(
    zaduznica_id: UUID,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.get(
        f"/api/zaduznice/{zaduznica_id}",
        headers=build_forward_headers(request, user),
    )
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Zaduznica not found")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/zaduznice/predlog", response_model=dict)
async def suggest_zaduznica_assignment(
    payload: dict,
    request: Request,
    user: dict = Depends(get_current_user),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.post(
        "/api/zaduznice/predlog",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
