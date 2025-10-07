from __future__ import annotations

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app_common.db import get_db

from ..dependencies import UserContext, require_roles
from ..models.enums import Role, TrebovanjeStatus
from ..repositories.trebovanje import TrebovanjeRepository
from ..schemas import TrebovanjeDetail, TrebovanjeImportPayload, TrebovanjeListResponse

router = APIRouter()


@router.get("/trebovanja", response_model=TrebovanjeListResponse)
async def list_trebovanja(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[TrebovanjeStatus] = Query(default=None, alias="status"),
    magacin_id: Optional[UUID] = None,
    radnja_id: Optional[UUID] = None,
    search: Optional[str] = None,
    db=Depends(get_db),
) -> TrebovanjeListResponse:
    repo = TrebovanjeRepository(db)
    return await repo.list(
        page=page,
        page_size=page_size,
        status=status_filter,
        magacin_id=magacin_id,
        radnja_id=radnja_id,
        search=search,
    )


@router.get("/trebovanja/{trebovanje_id}", response_model=TrebovanjeDetail)
async def get_trebovanje(trebovanje_id: UUID, db=Depends(get_db)) -> TrebovanjeDetail:
    repo = TrebovanjeRepository(db)
    try:
        return await repo.get(trebovanje_id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/trebovanja/import", response_model=TrebovanjeDetail, status_code=status.HTTP_201_CREATED)
async def import_trebovanje(
    payload: TrebovanjeImportPayload,
    user: UserContext = Depends(require_roles(Role.komercijalista, Role.sef)),
    db=Depends(get_db),
) -> TrebovanjeDetail:
    repo = TrebovanjeRepository(db)
    try:
        return await repo.create_from_import(payload, initiated_by=user.id)
    except ValueError as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
