from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app_common.db import get_db

from .auth_test import require_role
from .teams import get_any_user
from ..models.enums import Role
from ..schemas import (
    ManualCompleteRequest,
    SchedulerSuggestionRequest,
    SchedulerSuggestionResponse,
    ScanRequest,
    WorkerTask,
    WorkerTaskDetail,
    ZaduznicaCreateRequest,
    ZaduznicaCreateResponse,
    ZaduznicaDetail,
    ZaduznicaReassignRequest,
    ZaduznicaStatusUpdate,
)
from ..services import zaduznice as service
from ..services.scheduler import SchedulerService

router = APIRouter()

view_roles_dependency = require_role("sef")  # Simplified for now


@router.post("/zaduznice", response_model=ZaduznicaCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_zaduznice(
    payload: ZaduznicaCreateRequest,
    user: dict = Depends(get_any_user),
    db=Depends(get_db),
) -> ZaduznicaCreateResponse:
    # Check if user has permission (device tokens have role in user dict)
    if user.get("role") not in ["ADMIN", "SEF", "MENADZER"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only ADMIN, SEF, and MENADZER can create zaduznice")
    
    try:
        # For device tokens, use None as actor_id, for user tokens use user.id
        actor_id = None if user.get("device_id") else UUID(user["id"])
        created = await service.create_zaduznice(db, payload, actor_id=actor_id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ZaduznicaCreateResponse(zaduznica_ids=created)


@router.patch("/zaduznice/{zaduznica_id}/status", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def update_status(
    zaduznica_id: UUID,
    payload: ZaduznicaStatusUpdate,
    user: dict = Depends(require_role("sef")),
    db=Depends(get_db),
) -> None:
    try:
        await service.update_zaduznica_status(db, zaduznica_id, payload.status, actor_id=UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/zaduznice/{zaduznica_id}/reassign", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def reassign(
    zaduznica_id: UUID,
    payload: ZaduznicaReassignRequest,
    user: dict = Depends(require_role("sef")),
    db=Depends(get_db),
) -> None:
    try:
        await service.reassign_zaduznica(db, zaduznica_id, payload.target_magacioner_id, actor_id=UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/moji-zadaci", response_model=list[WorkerTask])
async def my_tasks(
    user: dict = Depends(get_any_user),
    db=Depends(get_db),
) -> list[WorkerTask]:
    # For device tokens, we need to get the actual worker ID from the token
    if user.get("device_id"):
        # Device tokens can't access worker tasks directly
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Device tokens cannot access worker tasks")
    
    return await service.list_worker_tasks(db, UUID(user["id"]))


@router.get("/moji-zadaci/{zaduznica_id}", response_model=WorkerTaskDetail)
async def my_task_detail(
    zaduznica_id: UUID,
    user: dict = Depends(require_role("magacioner")),
    db=Depends(get_db),
) -> WorkerTaskDetail:
    try:
        return await service.worker_task_detail(db, zaduznica_id, UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/scan/{zaduznica_stavka_id}", status_code=status.HTTP_202_ACCEPTED)
async def scan_item(
    zaduznica_stavka_id: UUID,
    payload: ScanRequest,
    user: dict = Depends(require_role("magacioner")),
    db=Depends(get_db),
) -> None:
    try:
        await service.register_scan(db, zaduznica_stavka_id, payload, actor_id=UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/complete-manual/{zaduznica_stavka_id}", status_code=status.HTTP_202_ACCEPTED)
async def manual_complete(
    zaduznica_stavka_id: UUID,
    payload: ManualCompleteRequest,
    user: dict = Depends(require_role("magacioner")),
    db=Depends(get_db),
) -> None:
    try:
        await service.manual_complete(db, zaduznica_stavka_id, payload, actor_id=UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/zaduznice/{zaduznica_id}", response_model=ZaduznicaDetail)
async def zaduznica_detail(
    zaduznica_id: UUID,
    _: UserContext = Depends(view_roles_dependency),
    db=Depends(get_db),
) -> ZaduznicaDetail:
    try:
        return await service.zaduznica_detail(db, zaduznica_id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
@router.post("/zaduznice/predlog", response_model=SchedulerSuggestionResponse)
async def suggest_zaduznica_assignment(
    payload: SchedulerSuggestionRequest,
    user: dict = Depends(require_role("sef")),
    db=Depends(get_db),
) -> SchedulerSuggestionResponse:
    scheduler = SchedulerService(db)
    try:
        log_entry, cached = await scheduler.suggest(payload.trebovanje_id, actor_id=UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return SchedulerSuggestionResponse(
        log_id=log_entry.id,
        trebovanje_id=log_entry.trebovanje_id,
        magacioner_id=log_entry.magacioner_id,
        score=float(log_entry.score),
        reason=log_entry.reason,
        lock_expires_at=log_entry.lock_expires_at,
        cached=cached,
    )


@router.post(
    "/zaduznice/predlog/{trebovanje_id}/cancel",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    response_model=None,
)
async def cancel_scheduler_suggestion(
    trebovanje_id: UUID,
    user: dict = Depends(require_role("sef")),
    db=Depends(get_db),
) -> None:
    scheduler = SchedulerService(db)
    try:
        await service.cancel_trebovanje_assignments(db, trebovanje_id, actor_id=UUID(user["id"]))
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await scheduler.cancel_suggestion(trebovanje_id, actor_id=UUID(user["id"]))
