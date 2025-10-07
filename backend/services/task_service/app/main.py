from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .routers import health, internal_catalog, trebovanja, tv, zaduznice

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Task Service", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(trebovanja.router, prefix="/api", tags=["trebovanja"])
app.include_router(zaduznice.router, prefix="/api", tags=["zaduznice"])
app.include_router(tv.router, prefix="/api", tags=["tv"])
app.include_router(internal_catalog.router, tags=["catalog"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("task-service.startup")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("task-service.shutdown")
