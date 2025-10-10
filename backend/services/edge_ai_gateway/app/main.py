from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio
import logging
from datetime import datetime

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .edge_ai_manager import EdgeAIManager
from .routers import health, inference, status, sync

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Edge AI Gateway", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

# Initialize edge AI manager
edge_ai_manager = EdgeAIManager()

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(inference.router, prefix="/api", tags=["inference"])
app.include_router(status.router, prefix="/api", tags=["status"])
app.include_router(sync.router, prefix="/api", tags=["sync"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize edge AI gateway service on startup."""
    logger.info("edge-ai-gateway.startup")
    
    # Initialize edge AI manager
    await edge_ai_manager.initialize()
    
    # Start background sync task
    asyncio.create_task(edge_ai_manager.background_sync_loop())
    
    logger.info("Edge AI gateway service initialized successfully")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("edge-ai-gateway.shutdown")
    
    # Stop background sync
    await edge_ai_manager.shutdown()
    
    logger.info("Edge AI gateway service shutdown complete")


# Make edge AI manager available to routers
app.state.edge_ai_manager = edge_ai_manager
