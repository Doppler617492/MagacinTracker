from __future__ import annotations

from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..dependencies import build_forward_headers, get_task_client
from ..services.auth import get_current_user, require_role

router = APIRouter()


@router.get("/worker/my-team", response_model=dict | None)
async def get_worker_team(
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict | None:
    """Get the current worker's team information."""
    response = await client.get(
        "/api/worker/my-team",
        headers=build_forward_headers(request, user),
    )
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/worker/tasks", response_model=list[dict])
async def list_worker_tasks(
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> list[dict]:
    response = await client.get(
        "/api/moji-zadaci",
        headers=build_forward_headers(request, user),
    )
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.get("/worker/tasks/{zaduznica_id}", response_model=dict)
async def worker_task_detail(
    zaduznica_id: UUID,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    response = await client.get(
        f"/api/moji-zadaci/{zaduznica_id}",
        headers=build_forward_headers(request, user),
    )
    if response.status_code == 404:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/worker/tasks/{zaduznica_stavka_id}/scan", status_code=status.HTTP_202_ACCEPTED)
async def worker_scan(
    zaduznica_stavka_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> None:
    response = await client.post(
        f"/api/scan/{zaduznica_stavka_id}",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 202):
        raise HTTPException(status_code=response.status_code, detail=response.text)


@router.post("/worker/tasks/{zaduznica_stavka_id}/complete-manual", status_code=status.HTTP_202_ACCEPTED)
async def worker_manual_complete(
    zaduznica_stavka_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> None:
    response = await client.post(
        f"/api/complete-manual/{zaduznica_stavka_id}",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 202):
        raise HTTPException(status_code=response.status_code, detail=response.text)


@router.post("/worker/tasks/{stavka_id}/manual-entry", response_model=dict)
async def worker_manual_entry(
    stavka_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    """Manual quantity entry without barcode scanning."""
    response = await client.post(
        f"/api/worker/tasks/{stavka_id}/manual-entry",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/worker/tasks/{stavka_id}/pick-by-code", response_model=dict)
async def worker_pick_by_code(
    stavka_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    """Pick an item by barcode or SKU scan."""
    response = await client.post(
        f"/api/worker/tasks/{stavka_id}/pick-by-code",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/worker/tasks/{stavka_id}/short-pick", response_model=dict)
async def worker_short_pick(
    stavka_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    """Record a short pick (partial quantity)."""
    response = await client.post(
        f"/api/worker/tasks/{stavka_id}/short-pick",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/worker/tasks/{stavka_id}/not-found", response_model=dict)
async def worker_not_found(
    stavka_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    """Mark an item as not found."""
    response = await client.post(
        f"/api/worker/tasks/{stavka_id}/not-found",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.post("/worker/documents/{trebovanje_id}/complete", response_model=dict)
async def worker_complete_document(
    trebovanje_id: UUID,
    payload: dict,
    request: Request,
    user: dict = Depends(require_role("magacioner")),
    client: httpx.AsyncClient = Depends(get_task_client),
) -> dict:
    """Complete a trebovanje document."""
    response = await client.post(
        f"/api/worker/documents/{trebovanje_id}/complete",
        json=payload,
        headers=build_forward_headers(request, user),
    )
    if response.status_code not in (200, 201):
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()
