import socketio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Gauge
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .config import settings
from .routers import ai, auth, catalog, counts, edge, exceptions, health, import_router, kafka, kpi, pantheon_sync, reports, stream, task_analytics, teams, trebovanja, tv, worker, zaduznice
from .routers import user_management
from .dependencies.http import create_http_clients

configure_logging()
logger = get_logger(__name__)

api = FastAPI(title="Magacin API Gateway", version="0.1.0")

api.add_middleware(CorrelationIdMiddleware)
api.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:4173", 
        "http://localhost:5130",
        "http://localhost:5131",  # PWA
        "http://localhost:5132",  # TV
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(health.router, prefix=settings.api_prefix, tags=["health"])
api.include_router(auth.router, prefix=settings.api_prefix, tags=["auth"])
api.include_router(user_management.router, prefix=settings.api_prefix, tags=["user-management"])
api.include_router(catalog.router, prefix=settings.api_prefix, tags=["catalog"])
api.include_router(trebovanja.router, prefix=settings.api_prefix, tags=["trebovanja"])
api.include_router(zaduznice.router, prefix=settings.api_prefix, tags=["zaduznice"])
api.include_router(worker.router, prefix=settings.api_prefix, tags=["worker"])
api.include_router(tv.router, prefix=settings.api_prefix, tags=["tv"])
api.include_router(kpi.router, prefix=f"{settings.api_prefix}/kpi", tags=["kpi"])
api.include_router(ai.router, prefix=f"{settings.api_prefix}/ai", tags=["ai"])
api.include_router(kafka.router, prefix=settings.api_prefix, tags=["kafka"])
api.include_router(stream.router, prefix=settings.api_prefix, tags=["stream"])
api.include_router(teams.router, prefix=settings.api_prefix, tags=["teams"])
api.include_router(edge.router, prefix=settings.api_prefix, tags=["edge"])
api.include_router(reports.router, prefix=f"{settings.api_prefix}/reports", tags=["reports"])
api.include_router(task_analytics.router, prefix=f"{settings.api_prefix}", tags=["task-analytics"])
api.include_router(pantheon_sync.router, prefix=f"{settings.api_prefix}/pantheon", tags=["pantheon-sync"])
api.include_router(import_router.router, prefix=settings.api_prefix, tags=["import"])
api.include_router(counts.router, prefix=settings.api_prefix, tags=["counts"])
api.include_router(exceptions.router, prefix=settings.api_prefix, tags=["exceptions"])

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
async def connect(sid, environ, auth):  # noqa: D401
    logger.info("socket.connect", sid=sid)
    ws_connections_gauge.inc()


@sio.event
async def disconnect(sid):  # noqa: D401
    logger.info("socket.disconnect", sid=sid)
    ws_connections_gauge.dec()


@sio.event
async def tv_delta(sid, data):
    logger.info("socket.broadcast", extra={"event": "tv_delta", "payload": data})
    await sio.emit("tv_delta", data)


app = socketio.ASGIApp(sio, other_asgi_app=api, socketio_path="/ws")
