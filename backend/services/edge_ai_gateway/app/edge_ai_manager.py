import asyncio
import json
import logging
import os
import pickle
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import uuid

logger = logging.getLogger(__name__)


class InferenceType(Enum):
    WORKER_PERFORMANCE = "worker_performance"
    TASK_OPTIMIZATION = "task_optimization"
    LOAD_BALANCING = "load_balancing"
    ANOMALY_DETECTION = "anomaly_detection"
    RESOURCE_ALLOCATION = "resource_allocation"


@dataclass
class EdgeInferenceRequest:
    inference_type: InferenceType
    device_id: str
    warehouse_id: str
    input_data: Dict[str, Any]
    timestamp: datetime
    request_id: str


@dataclass
class EdgeInferenceResponse:
    request_id: str
    inference_type: InferenceType
    prediction: float
    confidence: float
    inference_time_ms: float
    model_version: str
    device_id: str
    timestamp: datetime
    recommendations: List[Dict[str, Any]]


class TinyTransformer:
    """
    Ultra-lightweight transformer model optimized for edge devices.
    Designed for ARM processors with minimal memory footprint.
    """
    
    def __init__(self, input_size: int = 8, hidden_size: int = 32, output_size: int = 1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Minimal transformer architecture
        self.embedding = np.random.randn(input_size, hidden_size) * 0.1
        self.attention_weights = np.random.randn(hidden_size, hidden_size) * 0.1
        self.output_projection = np.random.randn(hidden_size, output_size) * 0.1
        
        # Model metadata
        self.model_version = "1.0.0"
        self.trained = False
        self.last_updated = None
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through tiny transformer."""
        # Embedding
        embedded = np.dot(x, self.embedding)
        
        # Simplified attention (single head)
        attention_scores = np.dot(embedded, self.attention_weights)
        attention_output = np.tanh(attention_scores)
        
        # Output projection
        output = np.dot(attention_output, self.output_projection)
        
        return output
    
    def predict(self, input_data: np.ndarray) -> Tuple[float, float]:
        """Make prediction with confidence score."""
        start_time = time.time()
        
        # Forward pass
        prediction = self.forward(input_data)
        
        # Calculate inference time
        inference_time = (time.time() - start_time) * 1000
        
        # Simple confidence based on prediction magnitude
        confidence = min(0.95, 0.5 + abs(prediction[0]) * 0.5)
        
        return float(prediction[0]), confidence
    
    def save_model(self, filepath: str):
        """Save the tiny transformer model."""
        model_data = {
            'embedding': self.embedding,
            'attention_weights': self.attention_weights,
            'output_projection': self.output_projection,
            'model_version': self.model_version,
            'trained': self.trained,
            'last_updated': self.last_updated
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load the tiny transformer model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.embedding = model_data['embedding']
        self.attention_weights = model_data['attention_weights']
        self.output_projection = model_data['output_projection']
        self.model_version = model_data['model_version']
        self.trained = model_data['trained']
        self.last_updated = model_data['last_updated']


class YoloLite:
    """
    Lightweight object detection model for edge devices.
    Optimized for warehouse scenarios (workers, packages, equipment).
    """
    
    def __init__(self):
        self.model_version = "1.0.0"
        self.classes = ['worker', 'package', 'equipment', 'vehicle', 'obstacle']
        self.confidence_threshold = 0.5
        self.trained = False
    
    def detect(self, image_data: np.ndarray) -> List[Dict[str, Any]]:
        """Detect objects in image data."""
        start_time = time.time()
        
        # Mock detection for demonstration
        # In production, this would use a real lightweight YOLO model
        detections = []
        
        # Simulate object detection
        for i in range(np.random.randint(1, 5)):
            detection = {
                'class': np.random.choice(self.classes),
                'confidence': np.random.uniform(0.6, 0.95),
                'bbox': [
                    np.random.randint(0, 100),
                    np.random.randint(0, 100),
                    np.random.randint(100, 200),
                    np.random.randint(100, 200)
                ],
                'timestamp': datetime.utcnow().isoformat()
            }
            
            if detection['confidence'] > self.confidence_threshold:
                detections.append(detection)
        
        inference_time = (time.time() - start_time) * 1000
        
        return {
            'detections': detections,
            'inference_time_ms': inference_time,
            'model_version': self.model_version
        }


class EdgeAIManager:
    """
    Manages edge AI inference and model synchronization.
    Handles local inference, model updates, and device management.
    """
    
    def __init__(self, hub_url: str = "http://localhost:8003"):
        self.hub_url = hub_url
        self.device_id = f"edge_device_{uuid.uuid4().hex[:8]}"
        
        # AI models
        self.tiny_transformer = TinyTransformer()
        self.yolo_lite = YoloLite()
        
        # Model paths
        self.model_dir = "./models/edge"
        self.transformer_path = os.path.join(self.model_dir, "tiny_transformer.pkl")
        self.yolo_path = os.path.join(self.model_dir, "yolo_lite.pkl")
        
        # Sync configuration
        self.sync_interval = timedelta(minutes=30)
        self.last_sync = None
        self.sync_running = False
        
        # Performance tracking
        self.inference_history = []
        self.performance_metrics = {
            'total_inferences': 0,
            'average_inference_time': 0,
            'success_rate': 0,
            'model_accuracy': 0,
            'last_inference': None
        }
        
        # Device status
        self.device_status = {
            'device_id': self.device_id,
            'status': 'online',
            'cpu_usage': 0,
            'memory_usage': 0,
            'temperature': 0,
            'battery_level': 100,
            'network_status': 'connected',
            'last_heartbeat': datetime.utcnow()
        }
    
    async def initialize(self):
        """Initialize the edge AI manager."""
        logger.info(f"Initializing edge AI manager for device {self.device_id}")
        
        # Create model directory
        os.makedirs(self.model_dir, exist_ok=True)
        
        # Load existing models if available
        if os.path.exists(self.transformer_path):
            try:
                self.tiny_transformer.load_model(self.transformer_path)
                logger.info("Loaded existing tiny transformer model")
            except Exception as e:
                logger.warning(f"Failed to load transformer model: {e}")
        
        if os.path.exists(self.yolo_path):
            try:
                # YoloLite would load here
                logger.info("Loaded existing YOLO Lite model")
            except Exception as e:
                logger.warning(f"Failed to load YOLO model: {e}")
        
        # Try to sync with hub on startup
        try:
            await self.sync_with_hub()
        except Exception as e:
            logger.warning(f"Failed to sync with hub on startup: {e}")
        
        logger.info("Edge AI manager initialized successfully")
    
    async def shutdown(self):
        """Shutdown the edge AI manager."""
        logger.info("Shutting down edge AI manager")
        
        # Save models
        try:
            self.tiny_transformer.save_model(self.transformer_path)
            logger.info("Saved transformer model")
        except Exception as e:
            logger.error(f"Failed to save transformer model: {e}")
        
        self.sync_running = False
        logger.info("Edge AI manager shutdown complete")
    
    async def infer(self, request: EdgeInferenceRequest) -> EdgeInferenceResponse:
        """Perform edge AI inference."""
        try:
            start_time = time.time()
            
            # Prepare input data
            input_data = self._prepare_input_data(request.input_data, request.inference_type)
            
            # Perform inference based on type
            if request.inference_type == InferenceType.WORKER_PERFORMANCE:
                prediction, confidence = self.tiny_transformer.predict(input_data)
                recommendations = self._generate_worker_recommendations(prediction, request.input_data)
            
            elif request.inference_type == InferenceType.TASK_OPTIMIZATION:
                prediction, confidence = self.tiny_transformer.predict(input_data)
                recommendations = self._generate_task_recommendations(prediction, request.input_data)
            
            elif request.inference_type == InferenceType.LOAD_BALANCING:
                prediction, confidence = self.tiny_transformer.predict(input_data)
                recommendations = self._generate_load_balancing_recommendations(prediction, request.input_data)
            
            elif request.inference_type == InferenceType.ANOMALY_DETECTION:
                prediction, confidence = self.tiny_transformer.predict(input_data)
                recommendations = self._generate_anomaly_recommendations(prediction, request.input_data)
            
            elif request.inference_type == InferenceType.RESOURCE_ALLOCATION:
                prediction, confidence = self.tiny_transformer.predict(input_data)
                recommendations = self._generate_resource_recommendations(prediction, request.input_data)
            
            else:
                raise ValueError(f"Unsupported inference type: {request.inference_type}")
            
            # Calculate inference time
            inference_time = (time.time() - start_time) * 1000
            
            # Update performance metrics
            self._update_performance_metrics(inference_time, True)
            
            # Create response
            response = EdgeInferenceResponse(
                request_id=request.request_id,
                inference_type=request.inference_type,
                prediction=prediction,
                confidence=confidence,
                inference_time_ms=inference_time,
                model_version=self.tiny_transformer.model_version,
                device_id=self.device_id,
                timestamp=datetime.utcnow(),
                recommendations=recommendations
            )
            
            logger.info(f"Edge inference completed: {request.inference_type.value} in {inference_time:.2f}ms")
            
            return response
            
        except Exception as e:
            inference_time = (time.time() - start_time) * 1000
            self._update_performance_metrics(inference_time, False)
            
            logger.error(f"Edge inference failed: {e}")
            raise
    
    def _prepare_input_data(self, input_data: Dict[str, Any], inference_type: InferenceType) -> np.ndarray:
        """Prepare input data for inference."""
        # Extract relevant features based on inference type
        if inference_type == InferenceType.WORKER_PERFORMANCE:
            features = [
                input_data.get('current_tasks', 0) / 10.0,
                input_data.get('completed_tasks', 0) / 50.0,
                input_data.get('efficiency_score', 0.5),
                input_data.get('idle_time', 0.2),
                input_data.get('experience_level', 0.5),
                input_data.get('workload', 0.5),
                input_data.get('time_of_day', 12) / 24.0,
                input_data.get('day_of_week', 1) / 7.0
            ]
        
        elif inference_type == InferenceType.TASK_OPTIMIZATION:
            features = [
                input_data.get('task_complexity', 0.5),
                input_data.get('priority', 0.5),
                input_data.get('estimated_duration', 30) / 120.0,
                input_data.get('worker_skill', 0.5),
                input_data.get('current_load', 0.5),
                input_data.get('deadline_pressure', 0.5),
                input_data.get('resource_availability', 0.5),
                input_data.get('historical_performance', 0.5)
            ]
        
        else:
            # Default feature extraction
            features = [
                input_data.get('value1', 0.5),
                input_data.get('value2', 0.5),
                input_data.get('value3', 0.5),
                input_data.get('value4', 0.5),
                input_data.get('value5', 0.5),
                input_data.get('value6', 0.5),
                input_data.get('value7', 0.5),
                input_data.get('value8', 0.5)
            ]
        
        return np.array(features).reshape(1, -1)
    
    def _generate_worker_recommendations(self, prediction: float, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate worker performance recommendations."""
        recommendations = []
        
        if prediction > 0.8:
            recommendations.append({
                'type': 'high_performance',
                'message': 'Worker performing excellently',
                'action': 'maintain_current_workload',
                'priority': 'low'
            })
        elif prediction > 0.6:
            recommendations.append({
                'type': 'good_performance',
                'message': 'Worker performing well',
                'action': 'slight_increase_workload',
                'priority': 'medium'
            })
        elif prediction > 0.4:
            recommendations.append({
                'type': 'average_performance',
                'message': 'Worker performance is average',
                'action': 'provide_training',
                'priority': 'medium'
            })
        else:
            recommendations.append({
                'type': 'low_performance',
                'message': 'Worker needs assistance',
                'action': 'reduce_workload_and_support',
                'priority': 'high'
            })
        
        return recommendations
    
    def _generate_task_recommendations(self, prediction: float, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate task optimization recommendations."""
        recommendations = []
        
        if prediction > 0.7:
            recommendations.append({
                'type': 'optimal_assignment',
                'message': 'Task is optimally assigned',
                'action': 'proceed_as_planned',
                'priority': 'low'
            })
        else:
            recommendations.append({
                'type': 'suboptimal_assignment',
                'message': 'Task assignment could be improved',
                'action': 'consider_reassignment',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _generate_load_balancing_recommendations(self, prediction: float, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate load balancing recommendations."""
        recommendations = []
        
        if prediction > 0.8:
            recommendations.append({
                'type': 'balanced_load',
                'message': 'Load is well balanced',
                'action': 'maintain_current_distribution',
                'priority': 'low'
            })
        else:
            recommendations.append({
                'type': 'unbalanced_load',
                'message': 'Load balancing needed',
                'action': 'redistribute_tasks',
                'priority': 'high'
            })
        
        return recommendations
    
    def _generate_anomaly_recommendations(self, prediction: float, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate anomaly detection recommendations."""
        recommendations = []
        
        if prediction > 0.7:
            recommendations.append({
                'type': 'anomaly_detected',
                'message': 'Anomaly detected in system',
                'action': 'investigate_and_alert',
                'priority': 'high'
            })
        else:
            recommendations.append({
                'type': 'normal_operation',
                'message': 'System operating normally',
                'action': 'continue_monitoring',
                'priority': 'low'
            })
        
        return recommendations
    
    def _generate_resource_recommendations(self, prediction: float, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate resource allocation recommendations."""
        recommendations = []
        
        if prediction > 0.7:
            recommendations.append({
                'type': 'optimal_resources',
                'message': 'Resources are optimally allocated',
                'action': 'maintain_current_allocation',
                'priority': 'low'
            })
        else:
            recommendations.append({
                'type': 'suboptimal_resources',
                'message': 'Resource allocation needs adjustment',
                'action': 'reallocate_resources',
                'priority': 'medium'
            })
        
        return recommendations
    
    def _update_performance_metrics(self, inference_time: float, success: bool):
        """Update performance metrics."""
        self.performance_metrics['total_inferences'] += 1
        self.performance_metrics['last_inference'] = datetime.utcnow()
        
        # Update average inference time
        total_inferences = self.performance_metrics['total_inferences']
        current_avg = self.performance_metrics['average_inference_time']
        self.performance_metrics['average_inference_time'] = (
            (current_avg * (total_inferences - 1) + inference_time) / total_inferences
        )
        
        # Update success rate
        if success:
            current_success_rate = self.performance_metrics['success_rate']
            self.performance_metrics['success_rate'] = (
                (current_success_rate * (total_inferences - 1) + 1) / total_inferences
            )
        else:
            current_success_rate = self.performance_metrics['success_rate']
            self.performance_metrics['success_rate'] = (
                (current_success_rate * (total_inferences - 1)) / total_inferences
            )
        
        # Store inference history
        self.inference_history.append({
            'timestamp': datetime.utcnow(),
            'inference_time_ms': inference_time,
            'success': success
        })
        
        # Keep only last 1000 inferences
        if len(self.inference_history) > 1000:
            self.inference_history = self.inference_history[-1000:]
    
    async def sync_with_hub(self) -> Dict[str, Any]:
        """Synchronize with central AI hub."""
        if self.sync_running:
            return {'status': 'sync_in_progress'}
        
        self.sync_running = True
        sync_start = datetime.utcnow()
        
        try:
            logger.info("Starting sync with AI hub")
            
            # Mock sync with hub
            # In production, this would fetch latest models from the hub
            await asyncio.sleep(0.1)  # Simulate network delay
            
            # Update model version
            self.tiny_transformer.model_version = f"1.0.{int(sync_start.timestamp())}"
            self.tiny_transformer.last_updated = sync_start
            
            sync_duration = (datetime.utcnow() - sync_start).total_seconds() * 1000
            self.last_sync = datetime.utcnow()
            
            sync_result = {
                'status': 'success',
                'sync_duration_ms': sync_duration,
                'model_version': self.tiny_transformer.model_version,
                'sync_time': self.last_sync.isoformat()
            }
            
            logger.info(f"Sync completed successfully: {sync_result}")
            return sync_result
            
        except Exception as e:
            sync_duration = (datetime.utcnow() - sync_start).total_seconds() * 1000
            
            error_result = {
                'status': 'error',
                'error': str(e),
                'sync_duration_ms': sync_duration,
                'sync_time': datetime.utcnow().isoformat()
            }
            
            logger.error(f"Sync failed: {error_result}")
            return error_result
        
        finally:
            self.sync_running = False
    
    async def background_sync_loop(self):
        """Background task for periodic synchronization with hub."""
        logger.info("Starting background sync loop")
        
        while True:
            try:
                if self.should_sync():
                    await self.sync_with_hub()
                
                # Sleep for 5 minutes before checking again
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in background sync loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    def should_sync(self) -> bool:
        """Check if synchronization with hub is needed."""
        if not self.last_sync:
            return True
        
        return datetime.utcnow() - self.last_sync > self.sync_interval
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status."""
        # Update device status
        self.device_status.update({
            'cpu_usage': np.random.uniform(10, 80),  # Mock CPU usage
            'memory_usage': np.random.uniform(20, 70),  # Mock memory usage
            'temperature': np.random.uniform(30, 60),  # Mock temperature
            'battery_level': max(0, self.device_status['battery_level'] - np.random.uniform(0, 2)),
            'last_heartbeat': datetime.utcnow()
        })
        
        return self.device_status
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return {
            **self.performance_metrics,
            'inference_history_size': len(self.inference_history),
            'recent_inferences': [
                {
                    'timestamp': inf['timestamp'].isoformat(),
                    'inference_time_ms': inf['inference_time_ms'],
                    'success': inf['success']
                }
                for inf in self.inference_history[-10:]
            ]
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            'transformer': {
                'model_version': self.tiny_transformer.model_version,
                'trained': self.tiny_transformer.trained,
                'last_updated': self.tiny_transformer.last_updated.isoformat() if self.tiny_transformer.last_updated else None,
                'input_size': self.tiny_transformer.input_size,
                'hidden_size': self.tiny_transformer.hidden_size,
                'output_size': self.tiny_transformer.output_size
            },
            'yolo_lite': {
                'model_version': self.yolo_lite.model_version,
                'trained': self.yolo_lite.trained,
                'classes': self.yolo_lite.classes,
                'confidence_threshold': self.yolo_lite.confidence_threshold
            }
        }
