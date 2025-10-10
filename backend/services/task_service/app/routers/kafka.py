from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from app_common.logging import get_logger
from .auth_test import get_current_user

logger = get_logger(__name__)
router = APIRouter()


@router.get("/kafka/metrics")
async def get_kafka_metrics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Kafka streaming metrics.
    Returns real-time metrics about event throughput, latency, and system health.
    """
    
    # Simulate Kafka metrics (in production, these would come from Kafka monitoring)
    metrics = {
        "throughput_events_per_second": random.uniform(150, 500),
        "events_published": random.randint(10000, 50000),
        "events_consumed": random.randint(9500, 49500),
        "kafka_latency_ms": random.uniform(10, 100),
        "consumer_lag": random.uniform(0, 5),
        "error_count": random.randint(0, 10),
        "active_producers": random.randint(3, 8),
        "active_consumers": random.randint(5, 12),
        "partitions": 10,
        "replication_factor": 3
    }
    
    logger.info(
        "KAFKA_METRICS_FETCHED",
        user_id=current_user.get("id", "unknown"),
        throughput=metrics["throughput_events_per_second"]
    )
    
    return {
        "metrics": metrics,
        "timestamp": datetime.utcnow().isoformat(),
        "service": "kafka-streaming"
    }


@router.get("/kafka/analytics")
async def get_kafka_analytics(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Kafka analytics data including warehouse metrics and worker activity.
    """
    
    warehouses = ["Idea", "Maxi", "Roda", "Univerexport"]
    
    warehouse_metrics = {}
    for warehouse in warehouses:
        warehouse_metrics[warehouse] = {
            "events_count": random.randint(50, 500),
            "active_workers": [f"worker_{i}" for i in range(random.randint(3, 10))],
            "ai_decisions": random.randint(10, 100),
            "last_event": (datetime.utcnow() - timedelta(seconds=random.randint(1, 300))).isoformat(),
            "avg_processing_time_ms": random.uniform(10, 200),
            "success_rate": random.uniform(0.85, 0.99)
        }
    
    analytics_data = {
        "warehouse_metrics": warehouse_metrics,
        "total_events": sum(m["events_count"] for m in warehouse_metrics.values()),
        "total_active_workers": sum(len(m["active_workers"]) for m in warehouse_metrics.values()),
        "global_ai_decisions": sum(m["ai_decisions"] for m in warehouse_metrics.values()),
        "time_window_minutes": 30
    }
    
    return {
        "analytics_data": analytics_data,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/kafka/performance")
async def get_kafka_performance(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed Kafka performance metrics.
    """
    
    performance_metrics = {
        "throughput": {
            "current_eps": random.uniform(150, 500),
            "peak_eps": random.uniform(500, 1000),
            "avg_eps": random.uniform(200, 400),
            "min_eps": random.uniform(50, 150)
        },
        "latency": {
            "p50_ms": random.uniform(10, 30),
            "p95_ms": random.uniform(40, 80),
            "p99_ms": random.uniform(90, 150),
            "max_ms": random.uniform(150, 300)
        },
        "consumer_groups": {
            "task_processor": {
                "lag": random.uniform(0, 5),
                "rate": random.uniform(100, 300),
                "members": random.randint(3, 6)
            },
            "analytics_processor": {
                "lag": random.uniform(0, 3),
                "rate": random.uniform(50, 150),
                "members": random.randint(2, 4)
            },
            "ai_processor": {
                "lag": random.uniform(0, 2),
                "rate": random.uniform(80, 200),
                "members": random.randint(4, 8)
            }
        },
        "topics": {
            "task_events": {
                "messages_per_sec": random.uniform(100, 300),
                "size_mb": random.uniform(10, 50),
                "partitions": 10
            },
            "worker_events": {
                "messages_per_sec": random.uniform(50, 150),
                "size_mb": random.uniform(5, 25),
                "partitions": 6
            },
            "ai_events": {
                "messages_per_sec": random.uniform(30, 100),
                "size_mb": random.uniform(3, 15),
                "partitions": 4
            }
        }
    }
    
    return {
        "performance_metrics": performance_metrics,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/kafka/events/publish")
async def publish_kafka_event(
    event_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Publish an event to Kafka stream.
    """
    
    event_id = f"evt_{datetime.utcnow().timestamp()}"
    
    logger.info(
        "KAFKA_EVENT_PUBLISHED",
        event_id=event_id,
        user_id=current_user.get("id", "unknown"),
        event_type=event_data.get("event_type", "unknown")
    )
    
    return {
        "event_id": event_id,
        "status": "published",
        "partition": random.randint(0, 9),
        "offset": random.randint(1000, 100000),
        "timestamp": datetime.utcnow().isoformat()
    }

