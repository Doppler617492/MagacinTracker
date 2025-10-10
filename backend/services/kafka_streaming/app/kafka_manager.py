import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from collections import deque, defaultdict
from enum import Enum
import uuid
import time

# Mock Kafka client for demonstration
class MockKafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.messages = []
    
    async def send(self, topic: str, value: bytes, key: Optional[bytes] = None):
        self.messages.append({
            'topic': topic,
            'value': value,
            'key': key,
            'timestamp': datetime.utcnow()
        })
        return True
    
    async def flush(self):
        pass
    
    async def close(self):
        pass

class MockKafkaConsumer:
    def __init__(self, bootstrap_servers: str, topics: List[str], group_id: str):
        self.bootstrap_servers = bootstrap_servers
        self.topics = topics
        self.group_id = group_id
        self.messages = deque()
    
    async def poll(self, timeout_ms: int = 1000):
        if self.messages:
            return self.messages.popleft()
        return None
    
    async def commit(self):
        pass
    
    async def close(self):
        pass

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
    AI_DECISION = "ai_decision"
    TELEMETRY = "telemetry"
    SYSTEM_ALERT = "system_alert"
    EDGE_INFERENCE = "edge_inference"
    EDGE_STATUS = "edge_status"


@dataclass
class KafkaEvent:
    event_id: str
    event_type: EventType
    warehouse_id: str
    timestamp: datetime
    data: Dict[str, Any]
    correlation_id: Optional[str] = None
    schema_version: str = "1.0"
    source: str = "kafka_streaming"


class KafkaManager:
    """
    Manages Kafka streaming infrastructure for real-time event processing.
    Handles event publishing, consumption, and analytics.
    """
    
    def __init__(self, bootstrap_servers: str = "localhost:9092"):
        self.bootstrap_servers = bootstrap_servers
        
        # Kafka clients
        self.producer: Optional[MockKafkaProducer] = None
        self.consumers: Dict[str, MockKafkaConsumer] = {}
        
        # Topic configuration
        self.topics = {
            'events': 'magacin_events',
            'ai_decisions': 'magacin_ai_decisions',
            'telemetry': 'magacin_telemetry',
            'edge_inference': 'magacin_edge_inference',
            'analytics': 'magacin_analytics'
        }
        
        # Consumer groups
        self.consumer_groups = {
            'events': 'stream_processor',
            'ai_decisions': 'ai_engine',
            'telemetry': 'analytics_engine',
            'edge_inference': 'edge_processor',
            'analytics': 'dashboard_updater'
        }
        
        # Event processing
        self.event_queue = asyncio.Queue(maxsize=50000)
        self.analytics_queue = asyncio.Queue(maxsize=10000)
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
            EventType.AI_DECISION: [self._handle_ai_decision],
            EventType.TELEMETRY: [self._handle_telemetry],
            EventType.SYSTEM_ALERT: [self._handle_system_alert],
            EventType.EDGE_INFERENCE: [self._handle_edge_inference],
            EventType.EDGE_STATUS: [self._handle_edge_status]
        }
        
        # Analytics aggregations
        self.analytics_data = {
            'top_workers': defaultdict(int),
            'warehouse_metrics': defaultdict(lambda: {
                'events_count': 0,
                'last_event': None,
                'active_workers': set(),
                'ai_decisions': 0
            }),
            'anomalies': deque(maxlen=1000),
            'trends': defaultdict(lambda: deque(maxlen=100))
        }
        
        # Metrics
        self.metrics = {
            'events_published': 0,
            'events_consumed': 0,
            'events_processed': 0,
            'kafka_latency_ms': 0,
            'consumer_lag': 0,
            'throughput_events_per_second': 0,
            'error_count': 0,
            'last_event_time': None
        }
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)
    
    async def initialize(self):
        """Initialize Kafka manager."""
        try:
            # Initialize producer
            self.producer = MockKafkaProducer(self.bootstrap_servers)
            
            # Initialize consumers for each topic
            for topic_key, topic_name in self.topics.items():
                consumer = MockKafkaConsumer(
                    self.bootstrap_servers,
                    [topic_name],
                    self.consumer_groups[topic_key]
                )
                self.consumers[topic_key] = consumer
            
            logger.info("Kafka manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Kafka manager: {e}")
            raise
    
    async def shutdown(self):
        """Shutdown Kafka manager."""
        self.is_running = False
        
        # Close producer
        if self.producer:
            await self.producer.close()
        
        # Close consumers
        for consumer in self.consumers.values():
            await consumer.close()
        
        logger.info("Kafka manager shutdown complete")
    
    async def publish_event(self, event: KafkaEvent) -> bool:
        """Publish an event to Kafka."""
        try:
            if not self.producer:
                raise Exception("Kafka producer not initialized")
            
            # Determine topic based on event type
            topic = self._get_topic_for_event_type(event.event_type)
            
            # Serialize event
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'warehouse_id': event.warehouse_id,
                'timestamp': event.timestamp.isoformat(),
                'data': event.data,
                'correlation_id': event.correlation_id,
                'schema_version': event.schema_version,
                'source': event.source
            }
            
            # Publish to Kafka
            start_time = time.time()
            success = await self.producer.send(
                topic,
                json.dumps(event_data).encode('utf-8'),
                key=event.warehouse_id.encode('utf-8')
            )
            
            # Update metrics
            latency = (time.time() - start_time) * 1000
            self.metrics['events_published'] += 1
            self.metrics['kafka_latency_ms'] = latency
            self.metrics['last_event_time'] = datetime.utcnow()
            
            logger.debug(f"Published event {event.event_id} to topic {topic}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id}: {e}")
            self.metrics['error_count'] += 1
            return False
    
    def _get_topic_for_event_type(self, event_type: EventType) -> str:
        """Get the appropriate Kafka topic for an event type."""
        if event_type in [EventType.AI_PREDICTION, EventType.AI_ACTION, EventType.AI_DECISION]:
            return self.topics['ai_decisions']
        elif event_type == EventType.TELEMETRY:
            return self.topics['telemetry']
        elif event_type in [EventType.EDGE_INFERENCE, EventType.EDGE_STATUS]:
            return self.topics['edge_inference']
        else:
            return self.topics['events']
    
    async def event_processing_loop(self):
        """Main event processing loop."""
        logger.info("Starting Kafka event processing loop")
        self.is_running = True
        
        while self.is_running:
            try:
                # Poll for messages from all consumers
                for topic_key, consumer in self.consumers.items():
                    message = await consumer.poll(timeout_ms=100)
                    if message:
                        await self._process_kafka_message(message, topic_key)
                
                # Update throughput metrics
                self._update_throughput_metrics()
                
                # Brief sleep to prevent CPU spinning
                await asyncio.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in event processing loop: {e}")
                await asyncio.sleep(1)
    
    async def analytics_processing_loop(self):
        """Analytics processing loop."""
        logger.info("Starting analytics processing loop")
        
        while self.is_running:
            try:
                # Process analytics events
                processed_count = 0
                start_time = time.time()
                
                while not self.analytics_queue.empty() and processed_count < 100:
                    try:
                        event = await asyncio.wait_for(
                            self.analytics_queue.get(), 
                            timeout=0.1
                        )
                        
                        await self._process_analytics_event(event)
                        processed_count += 1
                        
                    except asyncio.TimeoutError:
                        break
                    except Exception as e:
                        logger.error(f"Error processing analytics event: {e}")
                
                # Update analytics metrics
                if processed_count > 0:
                    processing_time = (time.time() - start_time) * 1000
                    self.performance_history.append({
                        'timestamp': datetime.utcnow(),
                        'events_processed': processed_count,
                        'processing_time_ms': processing_time
                    })
                
                # Sleep briefly
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in analytics processing loop: {e}")
                await asyncio.sleep(1)
    
    async def _process_kafka_message(self, message: Dict[str, Any], topic_key: str):
        """Process a message from Kafka."""
        try:
            # Parse message
            event_data = json.loads(message['value'].decode('utf-8'))
            
            # Create KafkaEvent
            event = KafkaEvent(
                event_id=event_data['event_id'],
                event_type=EventType(event_data['event_type']),
                warehouse_id=event_data['warehouse_id'],
                timestamp=datetime.fromisoformat(event_data['timestamp']),
                data=event_data['data'],
                correlation_id=event_data.get('correlation_id'),
                schema_version=event_data.get('schema_version', '1.0'),
                source=event_data.get('source', 'kafka_streaming')
            )
            
            # Add to processing queue
            await self.event_queue.put(event)
            
            # Update metrics
            self.metrics['events_consumed'] += 1
            
            logger.debug(f"Processed Kafka message: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to process Kafka message: {e}")
            self.metrics['error_count'] += 1
    
    async def _process_analytics_event(self, event: KafkaEvent):
        """Process an event for analytics."""
        try:
            # Update analytics data
            self._update_analytics_data(event)
            
            # Check for anomalies
            await self._check_for_anomalies(event)
            
            # Update trends
            self._update_trends(event)
            
            logger.debug(f"Processed analytics event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to process analytics event: {e}")
    
    def _update_analytics_data(self, event: KafkaEvent):
        """Update analytics data with event information."""
        # Update top workers
        if 'worker_id' in event.data:
            worker_id = event.data['worker_id']
            self.analytics_data['top_workers'][worker_id] += 1
        
        # Update warehouse metrics
        warehouse_metrics = self.analytics_data['warehouse_metrics'][event.warehouse_id]
        warehouse_metrics['events_count'] += 1
        warehouse_metrics['last_event'] = event.timestamp
        
        if 'worker_id' in event.data:
            warehouse_metrics['active_workers'].add(event.data['worker_id'])
        
        if event.event_type in [EventType.AI_DECISION, EventType.AI_ACTION]:
            warehouse_metrics['ai_decisions'] += 1
    
    async def _check_for_anomalies(self, event: KafkaEvent):
        """Check for anomalies in the event stream."""
        # Simple anomaly detection based on event frequency
        warehouse_metrics = self.analytics_data['warehouse_metrics'][event.warehouse_id]
        
        # Check for high event frequency (potential overload)
        if warehouse_metrics['events_count'] > 1000:  # Threshold
            anomaly = {
                'type': 'high_event_frequency',
                'warehouse_id': event.warehouse_id,
                'severity': 'medium',
                'description': f"High event frequency detected: {warehouse_metrics['events_count']} events",
                'timestamp': event.timestamp,
                'event_id': event.event_id
            }
            
            self.analytics_data['anomalies'].append(anomaly)
            
            # Publish anomaly event
            anomaly_event = KafkaEvent(
                event_id=f"anomaly_{uuid.uuid4()}",
                event_type=EventType.SYSTEM_ALERT,
                warehouse_id=event.warehouse_id,
                timestamp=datetime.utcnow(),
                data=anomaly
            )
            
            await self.publish_event(anomaly_event)
    
    def _update_trends(self, event: KafkaEvent):
        """Update trend data."""
        # Update event type trends
        self.analytics_data['trends'][event.event_type.value].append({
            'timestamp': event.timestamp,
            'warehouse_id': event.warehouse_id,
            'data': event.data
        })
    
    def _update_throughput_metrics(self):
        """Update throughput metrics."""
        # Calculate events per second based on recent performance
        if len(self.performance_history) > 0:
            recent_events = list(self.performance_history)[-10:]  # Last 10 measurements
            total_events = sum(p['events_processed'] for p in recent_events)
            total_time = sum(p['processing_time_ms'] for p in recent_events) / 1000
            
            if total_time > 0:
                self.metrics['throughput_events_per_second'] = total_events / total_time
    
    # Event handlers
    async def _handle_task_created(self, event: KafkaEvent):
        """Handle task created events."""
        logger.info(f"Task created: {event.data.get('task_id')} in warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_task_completed(self, event: KafkaEvent):
        """Handle task completed events."""
        logger.info(f"Task completed: {event.data.get('task_id')} by worker {event.data.get('worker_id')}")
        await self.analytics_queue.put(event)
    
    async def _handle_task_assigned(self, event: KafkaEvent):
        """Handle task assigned events."""
        logger.info(f"Task assigned: {event.data.get('task_id')} to worker {event.data.get('worker_id')}")
        await self.analytics_queue.put(event)
    
    async def _handle_worker_login(self, event: KafkaEvent):
        """Handle worker login events."""
        logger.info(f"Worker logged in: {event.data.get('worker_id')} in warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_worker_logout(self, event: KafkaEvent):
        """Handle worker logout events."""
        logger.info(f"Worker logged out: {event.data.get('worker_id')} from warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_scan_event(self, event: KafkaEvent):
        """Handle scan events."""
        logger.debug(f"Scan event: {event.data.get('scan_data')} by worker {event.data.get('worker_id')}")
        await self.analytics_queue.put(event)
    
    async def _handle_ai_prediction(self, event: KafkaEvent):
        """Handle AI prediction events."""
        logger.info(f"AI prediction: {event.data.get('prediction_type')} for warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_ai_action(self, event: KafkaEvent):
        """Handle AI action events."""
        logger.info(f"AI action: {event.data.get('action_type')} in warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_ai_decision(self, event: KafkaEvent):
        """Handle AI decision events."""
        logger.info(f"AI decision: {event.data.get('decision_type')} in warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_telemetry(self, event: KafkaEvent):
        """Handle telemetry events."""
        logger.debug(f"Telemetry: {event.data.get('metric_type')} from warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_system_alert(self, event: KafkaEvent):
        """Handle system alert events."""
        logger.warning(f"System alert: {event.data.get('alert_message')} in warehouse {event.warehouse_id}")
        await self.analytics_queue.put(event)
    
    async def _handle_edge_inference(self, event: KafkaEvent):
        """Handle edge inference events."""
        logger.info(f"Edge inference: {event.data.get('inference_type')} from device {event.data.get('device_id')}")
        await self.analytics_queue.put(event)
    
    async def _handle_edge_status(self, event: KafkaEvent):
        """Handle edge status events."""
        logger.debug(f"Edge status: {event.data.get('status_type')} from device {event.data.get('device_id')}")
        await self.analytics_queue.put(event)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current Kafka metrics."""
        return {
            **self.metrics,
            'topics': list(self.topics.values()),
            'consumer_groups': list(self.consumer_groups.values()),
            'queue_sizes': {
                'event_queue': self.event_queue.qsize(),
                'analytics_queue': self.analytics_queue.qsize()
            },
            'analytics_data_size': {
                'top_workers': len(self.analytics_data['top_workers']),
                'warehouses': len(self.analytics_data['warehouse_metrics']),
                'anomalies': len(self.analytics_data['anomalies']),
                'trends': len(self.analytics_data['trends'])
            }
        }
    
    def get_analytics_data(self) -> Dict[str, Any]:
        """Get current analytics data."""
        return {
            'top_workers': dict(self.analytics_data['top_workers']),
            'warehouse_metrics': {
                warehouse_id: {
                    **metrics,
                    'active_workers': list(metrics['active_workers'])
                }
                for warehouse_id, metrics in self.analytics_data['warehouse_metrics'].items()
            },
            'anomalies': list(self.analytics_data['anomalies']),
            'trends': {
                trend_type: list(trend_data)
                for trend_type, trend_data in self.analytics_data['trends'].items()
            }
        }
    
    def get_performance_history(self) -> List[Dict[str, Any]]:
        """Get performance history."""
        return [
            {
                'timestamp': p['timestamp'].isoformat(),
                'events_processed': p['events_processed'],
                'processing_time_ms': p['processing_time_ms']
            }
            for p in self.performance_history
        ]
