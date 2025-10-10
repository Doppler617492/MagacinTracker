from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
import asyncio
import logging
from datetime import datetime

from app_common.logging import configure_logging, get_logger
from app_common.middleware import CorrelationIdMiddleware

from .kafka_manager import KafkaManager
from .routers import health, events, analytics, metrics

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Kafka Streaming", version="0.1.0")
app.add_middleware(CorrelationIdMiddleware)

# Initialize Kafka manager
kafka_manager = KafkaManager()

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(events.router, prefix="/api", tags=["events"])
app.include_router(analytics.router, prefix="/api", tags=["analytics"])
app.include_router(metrics.router, prefix="/api", tags=["metrics"])

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize Kafka streaming service on startup."""
    logger.info("kafka-streaming.startup")
    
    # Initialize Kafka manager
    await kafka_manager.initialize()
    
    # Start background processing tasks
    asyncio.create_task(kafka_manager.event_processing_loop())
    asyncio.create_task(kafka_manager.analytics_processing_loop())
    
    logger.info("Kafka streaming service initialized successfully")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Cleanup on shutdown."""
    logger.info("kafka-streaming.shutdown")
    
    # Stop background processing
    await kafka_manager.shutdown()
    
    logger.info("Kafka streaming service shutdown complete")


# Make Kafka manager available to routers
app.state.kafka_manager = kafka_manager
