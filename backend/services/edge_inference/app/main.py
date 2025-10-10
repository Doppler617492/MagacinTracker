from fastapi import FastAPI, HTTPException
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .edge_model import EdgeModelManager
from .routers import health, inference, sync

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Edge Inference", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

# Initialize edge model manager
edge_manager = EdgeModelManager()

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(inference.router, prefix="/api", tags=["inference"])
app.include_router(sync.router, prefix="/api", tags=["sync"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize edge inference service on startup."""
    logger.info("edge-inference.startup")
    
    # Initialize edge model manager
    await edge_manager.initialize()
    
    # Start background sync task
    asyncio.create_task(edge_manager.background_sync_loop())
    
    logger.info("Edge inference service initialized successfully")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("edge-inference.shutdown")
    
    # Stop background sync
    edge_manager.stop_background_sync()
    
    logger.info("Edge inference service shutdown complete")


# Make edge manager available to routers
app.state.edge_manager = edge_manager
