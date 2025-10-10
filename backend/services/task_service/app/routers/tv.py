from __future__ import annotations

from fastapi import APIRouter, Depends

from app_common.db import get_db

from .auth_test import get_current_user
from ..schemas import TvSnapshot
from ..services.tv import build_tv_snapshot

router = APIRouter()


@router.get("/tv/snapshot", response_model=TvSnapshot)
async def tv_snapshot(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
) -> TvSnapshot:
    """Get TV dashboard snapshot - accessible by all authenticated users"""
    return await build_tv_snapshot(db)
