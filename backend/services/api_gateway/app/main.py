import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .config import settings
from .routers import auth, catalog, health, import_router, trebovanja, tv, worker, zaduznice
from .dependencies.http import create_http_clients

configure_logging()
logger = get_logger(__name__)

api = FastAPI(title="Magacin API Gateway", version="0.1.0")

api.add_middleware(CorrelationIdMiddleware)
api.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
api.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
api.include_router(catalog.router, prefix=settings.api_prefix, tags=["catalog"])
api.include_router(trebovanja.router, prefix=settings.api_prefix, tags=["trebovanja"])
api.include_router(zaduznice.router, prefix=settings.api_prefix, tags=["zaduznice"])
api.include_router(worker.router, prefix=settings.api_prefix, tags=["worker"])
api.include_router(tv.router, prefix=settings.api_prefix, tags=["tv"])
api.include_router(import_router.router, prefix=settings.api_prefix, tags=["import"])

Instrumentator().instrument(api).expose(api, include_in_schema=False)


@api.get("/", include_in_schema=False)
async def root() -> JSONResponse:
    return JSONResponse({"service": "api-gateway", "status": "ok"})


@api.on_event("startup")
async def on_startup() -> None:
    api.state.http_clients = create_http_clients()
    logger.info("api-gateway.startup")


@api.on_event("shutdown")
async def on_shutdown() -> None:
    clients = getattr(api.state, "http_clients", {})
    for client in clients.values():
        await client.aclose()
    logger.info("api-gateway.shutdown")


sio = socketio.AsyncServer(async_mode="asgi", cors_allowed_origins=settings.cors_origins)
ws_connections_gauge = Gauge("socketio_connections", "Active Socket.IO connections")


@sio.event
async def connect(sid, environ):  # noqa: D401
    logger.info("socket.connect", sid=sid)
    ws_connections_gauge.inc()


@sio.event
async def disconnect(sid):  # noqa: D401
    logger.info("socket.disconnect", sid=sid)
    ws_connections_gauge.dec()


@sio.event
async def tv_delta(sid, data):
    logger.info("socket.broadcast", event="tv_delta", payload=data)
    await sio.emit("tv_delta", data)


app = socketio.ASGIApp(sio, other_asgi_app=api, socketio_path="/ws")
