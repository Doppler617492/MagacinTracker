from __future__ import annotations

from fastapi import APIRouter, Depends

from app_common.db import get_db

from ..dependencies import require_roles
from ..models.enums import Role
from ..schemas import TvSnapshot
from ..services.tv import build_tv_snapshot

router = APIRouter()


@router.get("/tv/snapshot", response_model=TvSnapshot)
async def tv_snapshot(
    _: object = Depends(require_roles(Role.menadzer, Role.sef)),
    db=Depends(get_db),
) -> TvSnapshot:
    return await build_tv_snapshot(db)
