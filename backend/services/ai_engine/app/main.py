from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .routers import health, ai_models, training, optimization

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin AI Engine", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ai_models.router, prefix="/api/ai", tags=["ai-models"])
app.include_router(training.router, prefix="/api/ai", tags=["training"])
app.include_router(optimization.router, prefix="/api/ai", tags=["optimization"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("ai-engine.startup")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("ai-engine.shutdown")
