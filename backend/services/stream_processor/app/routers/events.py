from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app_common.logging import get_logger
from ..stream_manager import StreamEvent, EventType

logger = get_logger(__name__)
router = APIRouter()


class EventPublishRequest(BaseModel):
    event_type: str
    warehouse_id: str
    data: Dict[str, Any]
    correlation_id: str = None


class EventPublishResponse(BaseModel):
    event_id: str
    status: str
    timestamp: datetime


@router.post("/events/publish", response_model=EventPublishResponse)
async def publish_event(
    request: Request,
    event_request: EventPublishRequest,
) -> EventPublishResponse:
    """
    Publish an event to the real-time stream.
    
    This endpoint allows publishing events that will be processed
    in real-time by the stream processor and AI decision engine.
    """
    try:
        # Get stream manager from app state
        stream_manager = request.app.state.stream_manager
        
        # Create stream event
        stream_event = StreamEvent(
            event_id=f"event_{int(datetime.utcnow().timestamp() * 1000)}",
            event_type=EventType(event_request.event_type),
            warehouse_id=event_request.warehouse_id,
            timestamp=datetime.utcnow(),
            data=event_request.data,
            correlation_id=event_request.correlation_id
        )
        
        # Publish event
        success = await stream_manager.publish_event(stream_event)
        
        if success:
            logger.info(
                "EVENT_PUBLISHED",
                event_id=stream_event.event_id,
                event_type=event_request.event_type,
                warehouse_id=event_request.warehouse_id
            )
            
            return EventPublishResponse(
                event_id=stream_event.event_id,
                status="published",
                timestamp=stream_event.timestamp
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to publish event")
        
    except ValueError as e:
        logger.error("EVENT_PUBLISH_ERROR", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid event type: {str(e)}")
    
    except Exception as e:
        logger.error("EVENT_PUBLISH_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Event publish failed: {str(e)}")


@router.get("/events/recent")
async def get_recent_events(
    request: Request,
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Get recent events from the stream.
    
    Returns the most recent events processed by the stream processor.
    """
    try:
        stream_manager = request.app.state.stream_manager
        recent_events = stream_manager.get_recent_events(limit)
        
        logger.info("RECENT_EVENTS_REQUESTED", limit=limit)
        
        return {
            'events': recent_events,
            'total_count': len(recent_events),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("RECENT_EVENTS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get recent events: {str(e)}")


@router.get("/events/worker-activity")
async def get_worker_activity(
    request: Request,
) -> Dict[str, Any]:
    """
    Get current worker activity data.
    
    Returns real-time information about worker activity across all warehouses.
    """
    try:
        stream_manager = request.app.state.stream_manager
        worker_activity = stream_manager.get_worker_activity()
        
        logger.info("WORKER_ACTIVITY_REQUESTED")
        
        return {
            'worker_activity': worker_activity,
            'total_workers': len(worker_activity),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("WORKER_ACTIVITY_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get worker activity: {str(e)}")


@router.get("/events/warehouse-load")
async def get_warehouse_load(
    request: Request,
) -> Dict[str, Any]:
    """
    Get current warehouse load data.
    
    Returns real-time information about load and activity across all warehouses.
    """
    try:
        stream_manager = request.app.state.stream_manager
        warehouse_load = stream_manager.get_warehouse_load()
        
        logger.info("WAREHOUSE_LOAD_REQUESTED")
        
        return {
            'warehouse_load': warehouse_load,
            'total_warehouses': len(warehouse_load),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("WAREHOUSE_LOAD_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get warehouse load: {str(e)}")


@router.post("/events/simulate")
async def simulate_events(
    request: Request,
    warehouse_id: str = "warehouse_1",
    event_count: int = 10,
) -> Dict[str, Any]:
    """
    Simulate events for testing purposes.
    
    This endpoint generates simulated events to test the stream processing pipeline.
    """
    try:
        stream_manager = request.app.state.stream_manager
        
        # Generate simulated events
        simulated_events = []
        event_types = [
            EventType.TASK_CREATED,
            EventType.TASK_COMPLETED,
            EventType.TASK_ASSIGNED,
            EventType.WORKER_LOGIN,
            EventType.SCAN_EVENT
        ]
        
        for i in range(event_count):
            event_type = event_types[i % len(event_types)]
            
            # Generate event data based on type
            if event_type == EventType.TASK_CREATED:
                event_data = {
                    'task_id': f'task_{i}',
                    'priority': 'normal',
                    'estimated_duration': 30
                }
            elif event_type == EventType.TASK_COMPLETED:
                event_data = {
                    'task_id': f'task_{i-1}',
                    'worker_id': f'worker_{i % 5}',
                    'completion_time': 25 + (i % 10)
                }
            elif event_type == EventType.TASK_ASSIGNED:
                event_data = {
                    'task_id': f'task_{i}',
                    'worker_id': f'worker_{i % 5}',
                    'assigned_at': datetime.utcnow().isoformat()
                }
            elif event_type == EventType.WORKER_LOGIN:
                event_data = {
                    'worker_id': f'worker_{i % 5}',
                    'login_time': datetime.utcnow().isoformat()
                }
            else:  # SCAN_EVENT
                event_data = {
                    'worker_id': f'worker_{i % 5}',
                    'scan_data': f'scan_{i}',
                    'scan_time': datetime.utcnow().isoformat()
                }
            
            # Create and publish event
            stream_event = StreamEvent(
                event_id=f"sim_event_{i}_{int(datetime.utcnow().timestamp() * 1000)}",
                event_type=event_type,
                warehouse_id=warehouse_id,
                timestamp=datetime.utcnow(),
                data=event_data
            )
            
            success = await stream_manager.publish_event(stream_event)
            if success:
                simulated_events.append(stream_event.event_id)
        
        logger.info("EVENTS_SIMULATED", warehouse_id=warehouse_id, event_count=event_count)
        
        return {
            'simulated_events': simulated_events,
            'warehouse_id': warehouse_id,
            'event_count': len(simulated_events),
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("EVENT_SIMULATION_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Event simulation failed: {str(e)}")
