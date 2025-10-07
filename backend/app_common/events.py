from __future__ import annotations

import json
from typing import Any, Dict

import redis.asyncio as aioredis

from .config import get_settings
from .logging import get_logger


async def publish(channel: str, message: Dict[str, Any]) -> None:
    settings = get_settings()
    client = aioredis.from_url(settings.redis_url)
    try:
        await client.publish(channel, json.dumps(message))
    except Exception as exc:  # noqa: BLE001
        get_logger("events").error("event.publish.failed", channel=channel, error=str(exc))
    finally:
        await client.close()
