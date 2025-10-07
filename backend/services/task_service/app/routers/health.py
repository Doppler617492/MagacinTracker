from fastapi import APIRouter

from app_common.db import SessionLocal
from app_common.health import check_health

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return await check_health(SessionLocal)
