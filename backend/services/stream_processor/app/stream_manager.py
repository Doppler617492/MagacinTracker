import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque
import redis
import aioredis
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(Enum):
    TASK_CREATED = "task_created"
    TASK_COMPLETED = "task_completed"
    TASK_ASSIGNED = "task_assigned"
    WORKER_LOGIN = "worker_login"
    WORKER_LOGOUT = "worker_logout"
    SCAN_EVENT = "scan_event"
    AI_PREDICTION = "ai_prediction"
    AI_ACTION = "ai_action"
    SYSTEM_ALERT = "system_alert"


@dataclass
class StreamEvent:
    event_id: str
    event_type: EventType
    warehouse_id: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    processed: bool = False


class StreamManager:
    """
    Manages real-time event streaming and processing.
    Uses Redis Streams for event distribution and processing.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[aioredis.Redis] = None
        
        # Stream configuration
        self.stream_name = "magacin_events"
        self.consumer_group = "stream_processor"
        self.consumer_name = "processor_1"
        
        # Event processing
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.processing_tasks = []
        self.is_running = False
        
        # Event handlers
        self.event_handlers: Dict[EventType, List[Callable]] = {
            EventType.TASK_CREATED: [self._handle_task_created],
            EventType.TASK_COMPLETED: [self._handle_task_completed],
            EventType.TASK_ASSIGNED: [self._handle_task_assigned],
            EventType.WORKER_LOGIN: [self._handle_worker_login],
            EventType.WORKER_LOGOUT: [self._handle_worker_logout],
            EventType.SCAN_EVENT: [self._handle_scan_event],
            EventType.AI_PREDICTION: [self._handle_ai_prediction],
            EventType.AI_ACTION: [self._handle_ai_action],
            EventType.SYSTEM_ALERT: [self._handle_system_alert]
        }
        
        # Metrics
        self.metrics = {
            'events_processed': 0,
            'events_per_second': 0,
            'average_processing_time': 0,
            'queue_size': 0,
            'last_event_time': None,
            'processing_errors': 0
        }
        
        # Event history for pattern analysis
        self.event_history = deque(maxlen=10000)
        self.worker_activity = {}
        self.warehouse_load = {}
    
    async def initialize(self):
        """Initialize the stream manager."""
        try:
            # Connect to Redis
            self.redis_client = aioredis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(
                    self.stream_name, 
                    self.consumer_group, 
                    id='0', 
                    mkstream=True
                )
            except aioredis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
            
            logger.info("Stream manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize stream manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown the stream manager."""
        self.is_running = False
        
        # Cancel all processing tasks
        for task in self.processing_tasks:
            task.cancel()
        
        # Close Redis connection
        if self.redis_client:
            await self.redis_client.close()
        
        logger.info("Stream manager shutdown complete")
    
    async def publish_event(self, event: StreamEvent) -> bool:
        """Publish an event to the stream."""
        try:
            if not self.redis_client:
                raise Exception("Redis client not initialized")
            
            # Convert event to stream format
            stream_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'warehouse_id': event.warehouse_id,
                'timestamp': event.timestamp.isoformat(),
                'data': json.dumps(event.data),
                'correlation_id': event.correlation_id or ''
            }
            
            # Publish to Redis stream
            message_id = await self.redis_client.xadd(
                self.stream_name,
                stream_data
            )
            
            # Update metrics
            self.metrics['last_event_time'] = datetime.utcnow()
            
            logger.debug(f"Published event {event.event_id} to stream: {message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            return False
    
    async def event_processing_loop(self):
        """Main event processing loop."""
        logger.info("Starting event processing loop")
        self.is_running = True
        
        while self.is_running:
            try:
                # Read events from Redis stream
                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    self.consumer_name,
                    {self.stream_name: '>'},
                    count=100,
                    block=1000  # 1 second timeout
                )
                
                for stream, stream_messages in messages:
                    for message_id, fields in stream_messages:
                        # Parse event
                        event = self._parse_stream_message(message_id, fields)
                        if event:
                            # Add to processing queue
                            await self.event_queue.put(event)
                            
                            # Acknowledge message
                            await self.redis_client.xack(
                                self.stream_name,
                                self.consumer_group,
                                message_id
                            )
                
                # Update queue size metric
                self.metrics['queue_size'] = self.event_queue.qsize()
                
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)
    
    async def ai_decision_loop(self):
        """AI decision making loop."""
        logger.info("Starting AI decision loop")
        
        while self.is_running:
            try:
                # Process events from queue
                processed_count = 0
                start_time = datetime.utcnow()
                
                while not self.event_queue.empty() and processed_count < 100:
                    try:
                        event = await asyncio.wait_for(
                            self.event_queue.get(), 
                            timeout=0.1
                        )
                        
                        await self._process_event(event)
                        processed_count += 1
                        
                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        self.metrics['processing_errors'] += 1
                
                # Update metrics
                if processed_count > 0:
                    processing_time = (datetime.utcnow() - start_time).total_seconds()
                    self.metrics['events_processed'] += processed_count
                    self.metrics['events_per_second'] = processed_count / processing_time
                    self.metrics['average_processing_time'] = processing_time / processed_count
                
                # Sleep briefly to prevent CPU spinning
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in AI decision loop: {e}")
                await asyncio.sleep(1)
    
    def _parse_stream_message(self, message_id: str, fields: Dict[str, bytes]) -> Optional[StreamEvent]:
        """Parse a Redis stream message into a StreamEvent."""
        try:
            # Convert bytes to strings
            parsed_fields = {}
            for key, value in fields.items():
                parsed_fields[key.decode()] = value.decode()
            
            # Create event
            event = StreamEvent(
                event_id=parsed_fields['event_id'],
                event_type=EventType(parsed_fields['event_type']),
                warehouse_id=parsed_fields['warehouse_id'],
                timestamp=datetime.fromisoformat(parsed_fields['timestamp']),
                data=json.loads(parsed_fields['data']),
                correlation_id=parsed_fields.get('correlation_id') or None
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Failed to parse stream message: {e}")
            return None
    
    async def _process_event(self, event: StreamEvent):
        """Process a single event."""
        try:
            # Add to event history
            self.event_history.append(event)
            
            # Update activity tracking
            self._update_activity_tracking(event)
            
            # Call event handlers
            handlers = self.event_handlers.get(event.event_type, [])
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler {handler.__name__}: {e}")
            
            # Mark as processed
            event.processed = True
            
            logger.debug(f"Processed event {event.event_id} of type {event.event_type.value}")
            
        except Exception as e:
            logger.error(f"Failed to process event {event.event_id}: {e}")
            self.metrics['processing_errors'] += 1
    
    def _update_activity_tracking(self, event: StreamEvent):
        """Update worker and warehouse activity tracking."""
        # Update worker activity
        if 'worker_id' in event.data:
            worker_id = event.data['worker_id']
            if worker_id not in self.worker_activity:
                self.worker_activity[worker_id] = {
                    'last_activity': event.timestamp,
                    'event_count': 0,
                    'warehouse_id': event.warehouse_id
                }
            
            self.worker_activity[worker_id]['last_activity'] = event.timestamp
            self.worker_activity[worker_id]['event_count'] += 1
        
        # Update warehouse load
        if event.warehouse_id not in self.warehouse_load:
            self.warehouse_load[event.warehouse_id] = {
                'event_count': 0,
                'last_event': event.timestamp,
                'active_workers': set()
            }
        
        self.warehouse_load[event.warehouse_id]['event_count'] += 1
        self.warehouse_load[event.warehouse_id]['last_event'] = event.timestamp
        
        if 'worker_id' in event.data:
            self.warehouse_load[event.warehouse_id]['active_workers'].add(event.data['worker_id'])
    
    # Event handlers
    async def _handle_task_created(self, event: StreamEvent):
        """Handle task created events."""
        logger.info(f"Task created: {event.data.get('task_id')} in warehouse {event.warehouse_id}")
        
        # Check for potential overload
        warehouse_load = self.warehouse_load.get(event.warehouse_id, {})
        if warehouse_load.get('event_count', 0) > 100:  # Threshold for overload
            await self._trigger_ai_alert(
                event.warehouse_id,
                "high_task_volume",
                f"High task volume detected: {warehouse_load['event_count']} events"
            )
    
    async def _handle_task_completed(self, event: StreamEvent):
        """Handle task completed events."""
        logger.info(f"Task completed: {event.data.get('task_id')} by worker {event.data.get('worker_id')}")
        
        # Update worker performance metrics
        worker_id = event.data.get('worker_id')
        if worker_id:
            # Calculate completion time if available
            completion_time = event.data.get('completion_time')
            if completion_time:
                await self._update_worker_performance(worker_id, completion_time)
    
    async def _handle_task_assigned(self, event: StreamEvent):
        """Handle task assigned events."""
        logger.info(f"Task assigned: {event.data.get('task_id')} to worker {event.data.get('worker_id')}")
    
    async def _handle_worker_login(self, event: StreamEvent):
        """Handle worker login events."""
        logger.info(f"Worker logged in: {event.data.get('worker_id')} in warehouse {event.warehouse_id}")
    
    async def _handle_worker_logout(self, event: StreamEvent):
        """Handle worker logout events."""
        logger.info(f"Worker logged out: {event.data.get('worker_id')} from warehouse {event.warehouse_id}")
    
    async def _handle_scan_event(self, event: StreamEvent):
        """Handle scan events."""
        logger.debug(f"Scan event: {event.data.get('scan_data')} by worker {event.data.get('worker_id')}")
    
    async def _handle_ai_prediction(self, event: StreamEvent):
        """Handle AI prediction events."""
        logger.info(f"AI prediction: {event.data.get('prediction_type')} for warehouse {event.warehouse_id}")
    
    async def _handle_ai_action(self, event: StreamEvent):
        """Handle AI action events."""
        logger.info(f"AI action: {event.data.get('action_type')} in warehouse {event.warehouse_id}")
    
    async def _handle_system_alert(self, event: StreamEvent):
        """Handle system alert events."""
        logger.warning(f"System alert: {event.data.get('alert_message')} in warehouse {event.warehouse_id}")
    
    async def _trigger_ai_alert(self, warehouse_id: str, alert_type: str, message: str):
        """Trigger an AI alert."""
        alert_event = StreamEvent(
            event_id=f"alert_{datetime.utcnow().timestamp()}",
            event_type=EventType.SYSTEM_ALERT,
            warehouse_id=warehouse_id,
            timestamp=datetime.utcnow(),
            data={
                'alert_type': alert_type,
                'alert_message': message,
                'severity': 'high'
            }
        )
        
        await self.publish_event(alert_event)
    
    async def _update_worker_performance(self, worker_id: str, completion_time: float):
        """Update worker performance metrics."""
        # This would integrate with the AI engine for performance tracking
        logger.debug(f"Updated performance for worker {worker_id}: {completion_time}s")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        return {
            **self.metrics,
            'active_workers': len(self.worker_activity),
            'active_warehouses': len(self.warehouse_load),
            'event_history_size': len(self.event_history)
        }
    
    def get_worker_activity(self) -> Dict[str, Any]:
        """Get worker activity data."""
        return {
            worker_id: {
                **data,
                'active_workers': list(data['active_workers']) if isinstance(data.get('active_workers'), set) else data.get('active_workers', [])
            }
            for worker_id, data in self.worker_activity.items()
        }
    
    def get_warehouse_load(self) -> Dict[str, Any]:
        """Get warehouse load data."""
        return {
            warehouse_id: {
                **data,
                'active_workers': list(data['active_workers']) if isinstance(data.get('active_workers'), set) else data.get('active_workers', [])
            }
            for warehouse_id, data in self.warehouse_load.items()
        }
    
    def get_recent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent events."""
        recent_events = list(self.event_history)[-limit:]
        return [
            {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'warehouse_id': event.warehouse_id,
                'timestamp': event.timestamp.isoformat(),
                'data': event.data,
                'processed': event.processed
            }
            for event in recent_events
        ]
