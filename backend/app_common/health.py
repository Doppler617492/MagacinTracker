from __future__ import annotations

from typing import Any, Dict, Optional

import redis.asyncio as aioredis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import get_settings


async def check_health(
    session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    redis_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute health checks for database and redis."""

    settings = get_settings()

    result: Dict[str, Any] = {
        "service": settings.app_name,
        "status": "ok",
        "dependencies": {},
    }

    # Database check
    if session_factory is not None:
        try:
            async with session_factory() as session:
                await session.execute(text("SELECT 1"))
            result["dependencies"]["database"] = {"status": "ok"}
        except Exception as exc:  # noqa: BLE001
            result["status"] = "degraded"
            result["dependencies"]["database"] = {"status": "error", "error": str(exc)}

    # Redis check
    redis_target = redis_url or settings.redis_url
    if redis_target:
        try:
            client = aioredis.from_url(redis_target)
            await client.ping()
            await client.close()
            result["dependencies"]["redis"] = {"status": "ok"}
        except Exception as exc:  # noqa: BLE001
            result["status"] = "degraded"
            result["dependencies"]["redis"] = {"status": "error", "error": str(exc)}

    return result
