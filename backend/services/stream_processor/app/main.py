from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio
import logging
from datetime import datetime

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .stream_manager import StreamManager
from .routers import health, events, metrics

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Stream Processor", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

# Initialize stream manager
stream_manager = StreamManager()

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize stream processor service on startup."""
    logger.info("stream-processor.startup")
    
    # Initialize stream manager
    await stream_manager.initialize()
    
    # Start background processing tasks
    asyncio.create_task(stream_manager.event_processing_loop())
    asyncio.create_task(stream_manager.ai_decision_loop())
    
    logger.info("Stream processor service initialized successfully")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("stream-processor.shutdown")
    
    # Stop background processing
    await stream_manager.shutdown()
    
    logger.info("Stream processor service shutdown complete")


# Make stream manager available to routers
app.state.stream_manager = stream_manager
