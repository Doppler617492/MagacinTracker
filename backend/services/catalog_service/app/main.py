from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .routers import catalog
from .services.sync import scheduler

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Catalog Service", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

app.include_router(catalog.router, prefix="/api")

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("catalog-service.startup")
    scheduler.start()


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("catalog-service.shutdown")
    await scheduler.stop()
