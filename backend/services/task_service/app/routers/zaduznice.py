from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app_common.db import get_db

from ..dependencies import UserContext, require_roles
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

view_roles_dependency = require_roles(Role.sef, Role.magacioner)


@router.post("/zaduznice", response_model=ZaduznicaCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_zaduznice(
    payload: ZaduznicaCreateRequest,
    user: UserContext = Depends(require_roles(Role.sef)),
    db=Depends(get_db),
) -> ZaduznicaCreateResponse:
    try:
        created = await service.create_zaduznice(db, payload, actor_id=user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return ZaduznicaCreateResponse(zaduznica_ids=created)


@router.patch("/zaduznice/{zaduznica_id}/status", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def update_status(
    zaduznica_id: UUID,
    payload: ZaduznicaStatusUpdate,
    user: UserContext = Depends(require_roles(Role.sef)),
    db=Depends(get_db),
) -> None:
    try:
        await service.update_zaduznica_status(db, zaduznica_id, payload.status, actor_id=user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/zaduznice/{zaduznica_id}/reassign", response_model=None, status_code=status.HTTP_204_NO_CONTENT)
async def reassign(
    zaduznica_id: UUID,
    payload: ZaduznicaReassignRequest,
    user: UserContext = Depends(require_roles(Role.sef)),
    db=Depends(get_db),
) -> None:
    try:
        await service.reassign_zaduznica(db, zaduznica_id, payload.target_magacioner_id, actor_id=user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/moji-zadaci", response_model=list[WorkerTask])
async def my_tasks(
    user: UserContext = Depends(require_roles(Role.magacioner)),
    db=Depends(get_db),
) -> list[WorkerTask]:
    return await service.list_worker_tasks(db, user.id)


@router.get("/moji-zadaci/{zaduznica_id}", response_model=WorkerTaskDetail)
async def my_task_detail(
    zaduznica_id: UUID,
    user: UserContext = Depends(require_roles(Role.magacioner)),
    db=Depends(get_db),
) -> WorkerTaskDetail:
    try:
        return await service.worker_task_detail(db, zaduznica_id, user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/scan/{zaduznica_stavka_id}", status_code=status.HTTP_202_ACCEPTED)
async def scan_item(
    zaduznica_stavka_id: UUID,
    payload: ScanRequest,
    user: UserContext = Depends(require_roles(Role.magacioner)),
    db=Depends(get_db),
) -> None:
    try:
        await service.register_scan(db, zaduznica_stavka_id, payload, actor_id=user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/complete-manual/{zaduznica_stavka_id}", status_code=status.HTTP_202_ACCEPTED)
async def manual_complete(
    zaduznica_stavka_id: UUID,
    payload: ManualCompleteRequest,
    user: UserContext = Depends(require_roles(Role.magacioner)),
    db=Depends(get_db),
) -> None:
    try:
        await service.manual_complete(db, zaduznica_stavka_id, payload, actor_id=user.id)
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
    user: UserContext = Depends(require_roles(Role.sef)),
    db=Depends(get_db),
) -> SchedulerSuggestionResponse:
    scheduler = SchedulerService(db)
    try:
        log_entry, cached = await scheduler.suggest(payload.trebovanje_id, actor_id=user.id)
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
