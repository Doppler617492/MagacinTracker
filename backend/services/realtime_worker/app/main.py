import asyncio
import json

import redis.asyncio as aioredis
import socketio

from app_common.logging import configure_logging, get_logger

from .config import settings

configure_logging()
logger = get_logger(__name__)

sio = socketio.AsyncClient()


async def ensure_socket_connected() -> None:
    if sio.connected:
        return
    await sio.connect(settings.socketio_url, socketio_path="/ws")
    logger.info("realtime-worker.socket.connected", url=settings.socketio_url)


async def handle_message(message: dict) -> None:
    await ensure_socket_connected()
    await sio.emit("tv_delta", message)
    logger.info("realtime-worker.emit", payload=message)


async def worker() -> None:
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = redis.pubsub()
    await pubsub.subscribe(settings.leaderboard_channel)
    logger.info("realtime-worker.start", channel=settings.leaderboard_channel)

    async for msg in pubsub.listen():
        if msg["type"] != "message":
            continue
        data = json.loads(msg["data"])
        await handle_message(data)


def run() -> None:
    try:
        asyncio.run(worker())
    except KeyboardInterrupt:
        logger.info("realtime-worker.stop")


if __name__ == "__main__":
    run()
