import numpy as np
import pickle
import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import json
import hashlib

logger = logging.getLogger(__name__)


class EdgeModel:
    """
    Lightweight model optimized for edge inference.
    Provides fast predictions with minimal resource usage.
    """
    
    def __init__(self, model_id: str, model_path: Optional[str] = None):
        self.model_id = model_id
        self.model_path = model_path or f"./models/edge_model_{model_id}.pkl"
        
        # Model parameters (simplified for edge deployment)
        self.weights = None
        self.biases = None
        self.feature_scaler = None
        self.model_metadata = {
            'version': 0,
            'last_updated': None,
            'accuracy': 0.0,
            'model_size': 0,
            'inference_count': 0
        }
        
        # Performance tracking
        self.inference_times = []
        self.max_inference_time = 200  # Target: <200ms
        
        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.load_model()
                logger.info(f"Loaded existing edge model: {model_id}")
            except Exception as e:
                logger.warning(f"Failed to load existing edge model {model_id}: {e}")
    
    def initialize_from_global_model(self, global_model_params: Dict[str, Any]):
        """Initialize edge model from global model parameters."""
        # Extract and simplify model parameters for edge deployment
        if 'weights' in global_model_params and 'biases' in global_model_params:
            # Use only the first few layers for faster inference
            self.weights = [np.array(w) for w in global_model_params['weights'][:2]]  # First 2 layers only
            self.biases = [np.array(b) for b in global_model_params['biases'][:2]]
            
            # Initialize feature scaler
            self.feature_scaler = {
                'mean': np.zeros(8),  # 8 input features
                'std': np.ones(8)
            }
            
            # Update metadata
            self.model_metadata.update({
                'version': global_model_params.get('version', 0),
                'last_updated': datetime.utcnow(),
                'accuracy': global_model_params.get('accuracy', 0.0),
                'model_size': sum(w.size + b.size for w, b in zip(self.weights, self.biases))
            })
            
            # Save model
            self.save_model()
            
            logger.info(f"Initialized edge model {self.model_id} from global model")
    
    def predict(self, features: np.ndarray) -> Dict[str, Any]:
        """Make fast prediction using the edge model."""
        if self.weights is None:
            raise ValueError("Edge model not initialized")
        
        start_time = datetime.utcnow()
        
        try:
            # Normalize features
            if self.feature_scaler:
                features = (features - self.feature_scaler['mean']) / self.feature_scaler['std']
            
            # Forward pass through simplified model
            current_input = features
            
            for i in range(len(self.weights)):
                z = np.dot(current_input, self.weights[i]) + self.biases[i]
                
                if i == len(self.weights) - 1:  # Output layer
                    a = self.sigmoid(z)
                else:  # Hidden layers
                    a = self.relu(z)
                
                current_input = a
            
            prediction = current_input[0] if current_input.ndim > 1 else current_input
            
            # Calculate inference time
            inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self.inference_times.append(inference_time)
            self.model_metadata['inference_count'] += 1
            
            # Keep only last 100 inference times for performance tracking
            if len(self.inference_times) > 100:
                self.inference_times = self.inference_times[-100:]
            
            result = {
                'prediction': float(prediction),
                'confidence': min(0.95, 0.7 + self.model_metadata['accuracy'] * 0.3),
                'inference_time_ms': inference_time,
                'model_version': self.model_metadata['version'],
                'edge_mode': True
            }
            
            # Log slow inference
            if inference_time > self.max_inference_time:
                logger.warning(f"Slow edge inference: {inference_time:.2f}ms (target: <{self.max_inference_time}ms)")
            
            return result
            
        except Exception as e:
            inference_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            logger.error(f"Edge inference error: {e}")
            
            return {
                'prediction': 0.5,  # Default prediction
                'confidence': 0.1,
                'inference_time_ms': inference_time,
                'error': str(e),
                'edge_mode': True
            }
    
    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -250, 250)))
    
    def save_model(self):
        """Save the edge model to disk."""
        model_data = {
            'weights': [w.tolist() for w in self.weights] if self.weights else None,
            'biases': [b.tolist() for b in self.biases] if self.biases else None,
            'feature_scaler': self.feature_scaler,
            'model_metadata': self.model_metadata,
            'inference_times': self.inference_times[-50:]  # Keep last 50 for performance tracking
        }
        
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self):
        """Load the edge model from disk."""
        with open(self.model_path, 'rb') as f:
            model_data = pickle.load(f)
        
        if model_data['weights']:
            self.weights = [np.array(w) for w in model_data['weights']]
        if model_data['biases']:
            self.biases = [np.array(b) for b in model_data['biases']]
        
        self.feature_scaler = model_data.get('feature_scaler')
        self.model_metadata = model_data.get('model_metadata', {})
        self.inference_times = model_data.get('inference_times', [])
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the edge model."""
        if not self.inference_times:
            return {
                'avg_inference_time_ms': 0,
                'max_inference_time_ms': 0,
                'min_inference_time_ms': 0,
                'total_inferences': 0,
                'performance_target_met': True
            }
        
        avg_time = np.mean(self.inference_times)
        max_time = np.max(self.inference_times)
        min_time = np.min(self.inference_times)
        
        return {
            'avg_inference_time_ms': float(avg_time),
            'max_inference_time_ms': float(max_time),
            'min_inference_time_ms': float(min_time),
            'total_inferences': len(self.inference_times),
            'performance_target_met': avg_time < self.max_inference_time,
            'model_size_kb': self.model_metadata.get('model_size', 0) * 4 / 1024,  # 4 bytes per float
            'model_version': self.model_metadata.get('version', 0),
            'last_updated': self.model_metadata.get('last_updated', datetime.utcnow()).isoformat()
        }
    
    def is_initialized(self) -> bool:
        """Check if the edge model is initialized and ready for inference."""
        return self.weights is not None and self.biases is not None


class EdgeModelManager:
    """
    Manager for edge models and synchronization with central AI hub.
    Handles model updates, caching, and performance optimization.
    """
    
    def __init__(self, hub_url: str = "http://localhost:8003"):
        self.hub_url = hub_url
        self.models: Dict[str, EdgeModel] = {}
        self.sync_interval = timedelta(minutes=15)  # Sync every 15 minutes
        self.last_sync = None
        self.sync_running = False
        self.background_task = None
        
        # Performance tracking
        self.total_predictions = 0
        self.cache_hits = 0
        self.sync_errors = 0
    
    async def initialize(self):
        """Initialize the edge model manager."""
        logger.info("Initializing edge model manager")
        
        # Create default model if none exists
        if 'default' not in self.models:
            self.models['default'] = EdgeModel('default')
        
        # Try to sync with hub on startup
        try:
            await self.sync_with_hub()
        except Exception as e:
            logger.warning(f"Failed to sync with hub on startup: {e}")
        
        logger.info("Edge model manager initialized")
    
    async def sync_with_hub(self) -> Dict[str, Any]:
        """Synchronize edge models with the central AI hub."""
        if self.sync_running:
            logger.warning("Sync already in progress")
            return {'status': 'sync_in_progress'}
        
        self.sync_running = True
        sync_start = datetime.utcnow()
        
        try:
            logger.info("Starting sync with AI hub")
            
            # Get latest global model from hub
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.hub_url}/api/ai/federated/global-model") as response:
                    if response.status == 200:
                        global_model = await response.json()
                        
                        # Update edge models
                        for model_id, model in self.models.items():
                            model.initialize_from_global_model(global_model)
                        
                        sync_duration = (datetime.utcnow() - sync_start).total_seconds() * 1000
                        self.last_sync = datetime.utcnow()
                        
                        sync_result = {
                            'status': 'success',
                            'models_updated': len(self.models),
                            'sync_duration_ms': sync_duration,
                            'global_model_version': global_model.get('version', 0),
                            'sync_time': self.last_sync.isoformat()
                        }
                        
                        logger.info(f"Sync completed successfully: {sync_result}")
                        return sync_result
                    
                    else:
                        raise Exception(f"Hub responded with status {response.status}")
        
        except Exception as e:
            self.sync_errors += 1
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
    
    def stop_background_sync(self):
        """Stop the background synchronization task."""
        if self.background_task:
            self.background_task.cancel()
            logger.info("Background sync task stopped")
    
    def predict(self, model_id: str, features: List[float]) -> Dict[str, Any]:
        """Make prediction using the specified edge model."""
        if model_id not in self.models:
            raise ValueError(f"Model {model_id} not found")
        
        model = self.models[model_id]
        
        if not model.is_initialized():
            raise ValueError(f"Model {model_id} not initialized")
        
        # Convert features to numpy array
        features_array = np.array(features).reshape(1, -1)
        
        # Make prediction
        result = model.predict(features_array)
        
        # Update statistics
        self.total_predictions += 1
        
        return result
    
    def get_model_status(self, model_id: str) -> Dict[str, Any]:
        """Get status of a specific edge model."""
        if model_id not in self.models:
            return {'error': f'Model {model_id} not found'}
        
        model = self.models[model_id]
        
        return {
            'model_id': model_id,
            'is_initialized': model.is_initialized(),
            'performance_stats': model.get_performance_stats(),
            'model_metadata': model.model_metadata
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall edge inference system status."""
        model_statuses = {}
        for model_id, model in self.models.items():
            model_statuses[model_id] = self.get_model_status(model_id)
        
        return {
            'total_models': len(self.models),
            'initialized_models': sum(1 for m in self.models.values() if m.is_initialized()),
            'total_predictions': self.total_predictions,
            'sync_errors': self.sync_errors,
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'should_sync': self.should_sync(),
            'sync_running': self.sync_running,
            'models': model_statuses
        }
    
    def force_sync(self) -> Dict[str, Any]:
        """Force immediate synchronization with hub."""
        return asyncio.create_task(self.sync_with_hub())
