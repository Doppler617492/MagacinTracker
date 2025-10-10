from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request

from app_common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/metrics")
async def get_stream_metrics(
    request: Request,
) -> Dict[str, Any]:
    """
    Get real-time stream processing metrics.
    
    Returns performance metrics for the stream processor including
    throughput, latency, and processing statistics.
    """
    try:
        stream_manager = request.app.state.stream_manager
        metrics = stream_manager.get_metrics()
        
        logger.info("STREAM_METRICS_REQUESTED")
        
        return {
            'metrics': metrics,
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'stream-processor'
        }
        
    except Exception as e:
        logger.error("STREAM_METRICS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get stream metrics: {str(e)}")


@router.get("/metrics/throughput")
async def get_throughput_metrics(
    request: Request,
) -> Dict[str, Any]:
    """
    Get throughput-specific metrics.
    
    Returns detailed throughput metrics including events per second,
    processing rates, and queue statistics.
    """
    try:
        stream_manager = request.app.state.stream_manager
        metrics = stream_manager.get_metrics()
        
        throughput_metrics = {
            'events_per_second': metrics.get('events_per_second', 0),
            'events_processed_total': metrics.get('events_processed', 0),
            'queue_size': metrics.get('queue_size', 0),
            'average_processing_time': metrics.get('average_processing_time', 0),
            'processing_errors': metrics.get('processing_errors', 0),
            'last_event_time': metrics.get('last_event_time'),
            'active_workers': metrics.get('active_workers', 0),
            'active_warehouses': metrics.get('active_warehouses', 0)
        }
        
        logger.info("THROUGHPUT_METRICS_REQUESTED")
        
        return {
            'throughput_metrics': throughput_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("THROUGHPUT_METRICS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get throughput metrics: {str(e)}")


@router.get("/metrics/performance")
async def get_performance_metrics(
    request: Request,
) -> Dict[str, Any]:
    """
    Get performance metrics for the stream processor.
    
    Returns performance statistics including latency, error rates,
    and system health indicators.
    """
    try:
        stream_manager = request.app.state.stream_manager
        metrics = stream_manager.get_metrics()
        
        # Calculate performance indicators
        events_processed = metrics.get('events_processed', 0)
        processing_errors = metrics.get('processing_errors', 0)
        error_rate = (processing_errors / max(1, events_processed)) * 100
        
        avg_processing_time = metrics.get('average_processing_time', 0)
        events_per_second = metrics.get('events_per_second', 0)
        
        performance_metrics = {
            'error_rate_percent': round(error_rate, 2),
            'average_processing_time_ms': round(avg_processing_time * 1000, 2),
            'events_per_second': round(events_per_second, 2),
            'queue_size': metrics.get('queue_size', 0),
            'system_health': 'healthy' if error_rate < 5 and avg_processing_time < 0.1 else 'degraded',
            'throughput_target_met': events_per_second > 100,  # Target: >100 events/s
            'latency_target_met': avg_processing_time < 0.1,   # Target: <100ms
            'error_rate_target_met': error_rate < 5            # Target: <5%
        }
        
        logger.info("PERFORMANCE_METRICS_REQUESTED")
        
        return {
            'performance_metrics': performance_metrics,
            'raw_metrics': metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("PERFORMANCE_METRICS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")


@router.get("/metrics/health")
async def get_health_metrics(
    request: Request,
) -> Dict[str, Any]:
    """
    Get health metrics for the stream processor.
    
    Returns health indicators and system status information.
    """
    try:
        stream_manager = request.app.state.stream_manager
        metrics = stream_manager.get_metrics()
        
        # Calculate health indicators
        events_processed = metrics.get('events_processed', 0)
        processing_errors = metrics.get('processing_errors', 0)
        queue_size = metrics.get('queue_size', 0)
        last_event_time = metrics.get('last_event_time')
        
        # Determine health status
        health_status = 'healthy'
        health_issues = []
        
        if processing_errors > events_processed * 0.05:  # >5% error rate
            health_status = 'degraded'
            health_issues.append('High error rate')
        
        if queue_size > 1000:  # Queue backing up
            health_status = 'degraded'
            health_issues.append('Queue backing up')
        
        if last_event_time:
            time_since_last_event = (datetime.utcnow() - last_event_time).total_seconds()
            if time_since_last_event > 300:  # No events for 5 minutes
                health_status = 'degraded'
                health_issues.append('No recent events')
        
        health_metrics = {
            'status': health_status,
            'issues': health_issues,
            'events_processed': events_processed,
            'processing_errors': processing_errors,
            'error_rate_percent': round((processing_errors / max(1, events_processed)) * 100, 2),
            'queue_size': queue_size,
            'last_event_time': last_event_time.isoformat() if last_event_time else None,
            'active_workers': metrics.get('active_workers', 0),
            'active_warehouses': metrics.get('active_warehouses', 0),
            'event_history_size': metrics.get('event_history_size', 0)
        }
        
        logger.info("HEALTH_METRICS_REQUESTED", status=health_status)
        
        return {
            'health_metrics': health_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("HEALTH_METRICS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get health metrics: {str(e)}")
