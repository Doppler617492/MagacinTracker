import asyncio
import json
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
import socketio
from fastapi import FastAPI
from prometheus_client import Counter, Gauge, start_http_server
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger

from .config import settings

configure_logging()
logger = get_logger(__name__)

# Prometheus metrics
messages_processed = Counter("realtime_messages_processed_total", "Total processed messages")
websocket_disconnections = Counter("websocket_disconnections_total", "Total WebSocket disconnections")
active_connections = Gauge("websocket_active_connections", "Active WebSocket connections")

sio = socketio.AsyncClient()


async def ensure_socket_connected() -> None:
    if sio.connected:
        return
    try:
        await sio.connect(settings.socketio_url, socketio_path="/ws")
        active_connections.inc()
        logger.info("realtime-worker.socket.connected", url=settings.socketio_url)
    except Exception as e:
        websocket_disconnections.inc()
        logger.error("realtime-worker.socket.connection_failed", error=str(e))
        raise


async def handle_message(message: dict) -> None:
    try:
        await ensure_socket_connected()
        await sio.emit("tv_delta", message)
        messages_processed.inc()
        logger.info("realtime-worker.emit", payload=message)
    except Exception as e:
        websocket_disconnections.inc()
        active_connections.dec()
        logger.error("realtime-worker.emit.failed", error=str(e))
        raise


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


# FastAPI app for metrics endpoint
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start Prometheus metrics server
    start_http_server(8004)
    logger.info("realtime-worker.metrics.start", port=8004)
    
    # Start worker task
    worker_task = asyncio.create_task(worker())
    
    yield
    
    # Cleanup
    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    logger.info("realtime-worker.stop")


app = FastAPI(title="Magacin Realtime Worker", version="0.1.0", lifespan=lifespan)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def run() -> None:
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)


if __name__ == "__main__":
    run()
