import numpy as np
import pickle
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
import hashlib
import threading
import time

logger = logging.getLogger(__name__)


class FederatedNode:
    """
    Federated learning node that participates in collaborative model training.
    Each node (warehouse/location) trains a local model and shares parameters.
    """
    
    def __init__(self, node_id: str, model_path: Optional[str] = None):
        self.node_id = node_id
        self.model_path = model_path or f"./models/federated_node_{node_id}.pkl"
        
        # Local model (simplified for federated learning)
        self.local_model = {
            'weights': None,
            'biases': None,
            'last_updated': None,
            'training_samples': 0,
            'node_id': node_id
        }
        
        # Federated learning parameters
        self.learning_rate = 0.01
        self.local_epochs = 5
        self.batch_size = 32
        
        # Synchronization state
        self.last_sync = None
        self.sync_frequency = timedelta(hours=1)  # Sync every hour
        self.is_syncing = False
        
        # Load existing model if available
        if os.path.exists(self.model_path):
            try:
                self.load_local_model()
                logger.info(f"Loaded existing federated model for node {node_id}")
            except Exception as e:
                logger.warning(f"Failed to load existing model for node {node_id}: {e}")
    
    def initialize_model(self, global_model_params: Dict[str, Any]):
        """Initialize local model with global parameters."""
        self.local_model['weights'] = [np.array(w) for w in global_model_params['weights']]
        self.local_model['biases'] = [np.array(b) for b in global_model_params['biases']]
        self.local_model['last_updated'] = datetime.utcnow()
        self.local_model['training_samples'] = 0
        
        logger.info(f"Initialized federated model for node {self.node_id}")
    
    def train_local_model(self, local_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Train the local model on node-specific data."""
        if not self.local_model['weights']:
            raise ValueError("Local model not initialized. Call initialize_model first.")
        
        logger.info(f"Training local model for node {self.node_id} with {len(local_data)} samples")
        
        # Prepare training data
        X, y = self.prepare_training_data(local_data)
        
        if len(X) == 0:
            logger.warning(f"No training data available for node {self.node_id}")
            return {'status': 'no_data', 'samples': 0}
        
        # Local training (simplified SGD)
        training_loss = 0.0
        training_accuracy = 0.0
        
        for epoch in range(self.local_epochs):
            # Shuffle data
            indices = np.random.permutation(len(X))
            X_shuffled = X[indices]
            y_shuffled = y[indices]
            
            epoch_loss = 0.0
            epoch_accuracy = 0.0
            
            # Mini-batch training
            for i in range(0, len(X_shuffled), self.batch_size):
                batch_X = X_shuffled[i:i+self.batch_size]
                batch_y = y_shuffled[i:i+self.batch_size]
                
                # Forward pass
                activations = self.forward_pass(batch_X)
                
                # Compute loss and accuracy
                batch_loss = self.compute_loss(activations[-1], batch_y)
                batch_accuracy = self.compute_accuracy(activations[-1], batch_y)
                
                epoch_loss += batch_loss
                epoch_accuracy += batch_accuracy
                
                # Backward pass and update
                self.backward_pass(batch_X, batch_y, activations)
            
            training_loss = epoch_loss / (len(X_shuffled) // self.batch_size)
            training_accuracy = epoch_accuracy / (len(X_shuffled) // self.batch_size)
        
        # Update model metadata
        self.local_model['last_updated'] = datetime.utcnow()
        self.local_model['training_samples'] = len(local_data)
        
        # Save local model
        self.save_local_model()
        
        training_summary = {
            'node_id': self.node_id,
            'status': 'completed',
            'samples': len(local_data),
            'epochs': self.local_epochs,
            'final_loss': training_loss,
            'final_accuracy': training_accuracy,
            'training_duration': self.local_epochs * len(local_data) / 1000,  # Mock duration
            'last_updated': self.local_model['last_updated'].isoformat()
        }
        
        logger.info(f"Local training completed for node {self.node_id}: Loss={training_loss:.4f}, Acc={training_accuracy:.4f}")
        
        return training_summary
    
    def prepare_training_data(self, local_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data for local model."""
        X = []
        y = []
        
        for record in local_data:
            # Simplified feature set for federated learning
            features = [
                record.get('current_tasks', 0) / 10.0,
                record.get('completed_tasks_today', 0) / 50.0,
                record.get('efficiency_score', 0.5),
                record.get('idle_time_percentage', 0.2),
                record.get('store_load_index', 0.5),
                record.get('day_of_week', 1) / 7.0,
                record.get('hour_of_day', 12) / 24.0,
                record.get('team_size', 1) / 10.0
            ]
            
            target = record.get('performance_score', 0.5)
            
            X.append(features)
            y.append([target])
        
        return np.array(X), np.array(y)
    
    def forward_pass(self, X: np.ndarray) -> List[np.ndarray]:
        """Forward pass through the local model."""
        activations = [X]
        current_input = X
        
        for i in range(len(self.local_model['weights'])):
            z = np.dot(current_input, self.local_model['weights'][i]) + self.local_model['biases'][i]
            
            if i == len(self.local_model['weights']) - 1:  # Output layer
                a = self.sigmoid(z)
            else:  # Hidden layers
                a = self.relu(z)
            
            activations.append(a)
            current_input = a
        
        return activations
    
    def backward_pass(self, X: np.ndarray, y: np.ndarray, activations: List[np.ndarray]):
        """Backward pass and parameter update."""
        m = X.shape[0]
        
        # Output layer gradient
        dz = activations[-1] - y
        dW = (1/m) * np.dot(activations[-2].T, dz)
        db = (1/m) * np.sum(dz, axis=0, keepdims=True)
        
        # Update parameters
        self.local_model['weights'][-1] -= self.learning_rate * dW
        self.local_model['biases'][-1] -= self.learning_rate * db
        
        # Hidden layers (simplified - only update last hidden layer)
        if len(self.local_model['weights']) > 1:
            da = np.dot(dz, self.local_model['weights'][-1].T)
            dz = da * self.relu_derivative(activations[-2])
            
            dW = (1/m) * np.dot(activations[-3].T, dz)
            db = (1/m) * np.sum(dz, axis=0, keepdims=True)
            
            self.local_model['weights'][-2] -= self.learning_rate * dW
            self.local_model['biases'][-2] -= self.learning_rate * db
    
    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)
    
    def relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """ReLU derivative."""
        return (x > 0).astype(float)
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -250, 250)))
    
    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute mean squared error loss."""
        m = y_true.shape[0]
        return (1/(2*m)) * np.sum(np.square(y_pred - y_true))
    
    def compute_accuracy(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute R² accuracy."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0, min(1, r_squared))
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get current model parameters for federated aggregation."""
        if not self.local_model['weights']:
            return None
        
        return {
            'node_id': self.node_id,
            'weights': [w.tolist() for w in self.local_model['weights']],
            'biases': [b.tolist() for b in self.local_model['biases']],
            'training_samples': self.local_model['training_samples'],
            'last_updated': self.local_model['last_updated'].isoformat() if self.local_model['last_updated'] else None
        }
    
    def update_model_parameters(self, global_params: Dict[str, Any]):
        """Update local model with aggregated global parameters."""
        self.local_model['weights'] = [np.array(w) for w in global_params['weights']]
        self.local_model['biases'] = [np.array(b) for b in global_params['biases']]
        self.local_model['last_updated'] = datetime.utcnow()
        
        # Save updated model
        self.save_local_model()
        
        logger.info(f"Updated federated model for node {self.node_id}")
    
    def save_local_model(self):
        """Save the local model to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, 'wb') as f:
            pickle.dump(self.local_model, f)
    
    def load_local_model(self):
        """Load the local model from disk."""
        with open(self.model_path, 'rb') as f:
            self.local_model = pickle.load(f)
    
    def should_sync(self) -> bool:
        """Check if the node should synchronize with the global model."""
        if not self.last_sync:
            return True
        
        return datetime.utcnow() - self.last_sync > self.sync_frequency
    
    def get_node_status(self) -> Dict[str, Any]:
        """Get the current status of the federated node."""
        return {
            'node_id': self.node_id,
            'is_initialized': self.local_model['weights'] is not None,
            'last_updated': self.local_model['last_updated'].isoformat() if self.local_model['last_updated'] else None,
            'training_samples': self.local_model['training_samples'],
            'last_sync': self.last_sync.isoformat() if self.last_sync else None,
            'should_sync': self.should_sync(),
            'is_syncing': self.is_syncing
        }


class FederatedAggregator:
    """
    Central aggregator that coordinates federated learning across multiple nodes.
    Implements Federated Averaging (FedAvg) algorithm.
    """
    
    def __init__(self, global_model_path: Optional[str] = None):
        self.global_model_path = global_model_path or "./models/global_federated_model.pkl"
        self.nodes: Dict[str, FederatedNode] = {}
        self.global_model = {
            'weights': None,
            'biases': None,
            'version': 0,
            'last_aggregated': None,
            'total_samples': 0
        }
        
        # Aggregation parameters
        self.min_nodes_for_aggregation = 3
        self.aggregation_frequency = timedelta(minutes=30)
        self.last_aggregation = None
        
        # Load existing global model
        if os.path.exists(self.global_model_path):
            try:
                self.load_global_model()
                logger.info("Loaded existing global federated model")
            except Exception as e:
                logger.warning(f"Failed to load existing global model: {e}")
    
    def register_node(self, node_id: str) -> FederatedNode:
        """Register a new federated learning node."""
        if node_id in self.nodes:
            logger.warning(f"Node {node_id} already registered")
            return self.nodes[node_id]
        
        node = FederatedNode(node_id)
        self.nodes[node_id] = node
        
        # Initialize with global model if available
        if self.global_model['weights']:
            node.initialize_model(self.global_model)
        
        logger.info(f"Registered federated node: {node_id}")
        return node
    
    def aggregate_models(self) -> Dict[str, Any]:
        """Aggregate local models using Federated Averaging."""
        if len(self.nodes) < self.min_nodes_for_aggregation:
            logger.warning(f"Not enough nodes for aggregation. Need {self.min_nodes_for_aggregation}, have {len(self.nodes)}")
            return {'status': 'insufficient_nodes', 'nodes': len(self.nodes)}
        
        # Collect model parameters from all nodes
        node_parameters = []
        total_samples = 0
        
        for node_id, node in self.nodes.items():
            if node.local_model['weights'] is None:
                continue
            
            params = node.get_model_parameters()
            if params:
                node_parameters.append(params)
                total_samples += params['training_samples']
        
        if len(node_parameters) < self.min_nodes_for_aggregation:
            logger.warning(f"Not enough trained nodes for aggregation. Need {self.min_nodes_for_aggregation}, have {len(node_parameters)}")
            return {'status': 'insufficient_trained_nodes', 'nodes': len(node_parameters)}
        
        logger.info(f"Aggregating models from {len(node_parameters)} nodes with {total_samples} total samples")
        
        # Federated Averaging
        aggregated_weights = []
        aggregated_biases = []
        
        # Initialize aggregated parameters
        first_params = node_parameters[0]
        for i in range(len(first_params['weights'])):
            weight_shape = np.array(first_params['weights'][i]).shape
            bias_shape = np.array(first_params['biases'][i]).shape
            
            aggregated_weights.append(np.zeros(weight_shape))
            aggregated_biases.append(np.zeros(bias_shape))
        
        # Weighted average based on training samples
        for params in node_parameters:
            weight = params['training_samples'] / total_samples
            
            for i in range(len(params['weights'])):
                aggregated_weights[i] += weight * np.array(params['weights'][i])
                aggregated_biases[i] += weight * np.array(params['biases'][i])
        
        # Update global model
        self.global_model['weights'] = [w.tolist() for w in aggregated_weights]
        self.global_model['biases'] = [b.tolist() for b in aggregated_biases]
        self.global_model['version'] += 1
        self.global_model['last_aggregated'] = datetime.utcnow()
        self.global_model['total_samples'] = total_samples
        
        # Save global model
        self.save_global_model()
        
        # Distribute updated model to all nodes
        self.distribute_global_model()
        
        aggregation_summary = {
            'status': 'completed',
            'nodes_participated': len(node_parameters),
            'total_samples': total_samples,
            'global_model_version': self.global_model['version'],
            'aggregation_time': datetime.utcnow().isoformat(),
            'participating_nodes': [p['node_id'] for p in node_parameters]
        }
        
        logger.info(f"Federated aggregation completed. Global model version: {self.global_model['version']}")
        
        return aggregation_summary
    
    def distribute_global_model(self):
        """Distribute the updated global model to all nodes."""
        for node_id, node in self.nodes.items():
            try:
                node.update_model_parameters(self.global_model)
                node.last_sync = datetime.utcnow()
                logger.info(f"Distributed global model to node {node_id}")
            except Exception as e:
                logger.error(f"Failed to distribute global model to node {node_id}: {e}")
    
    def should_aggregate(self) -> bool:
        """Check if it's time to perform model aggregation."""
        if not self.last_aggregation:
            return True
        
        return datetime.utcnow() - self.last_aggregation > self.aggregation_frequency
    
    def get_global_model_status(self) -> Dict[str, Any]:
        """Get the status of the global federated model."""
        node_statuses = {}
        for node_id, node in self.nodes.items():
            node_statuses[node_id] = node.get_node_status()
        
        return {
            'global_model': {
                'version': self.global_model['version'],
                'last_aggregated': self.global_model['last_aggregated'].isoformat() if self.global_model['last_aggregated'] else None,
                'total_samples': self.global_model['total_samples'],
                'is_initialized': self.global_model['weights'] is not None
            },
            'nodes': node_statuses,
            'aggregation_status': {
                'total_nodes': len(self.nodes),
                'trained_nodes': sum(1 for node in self.nodes.values() if node.local_model['weights'] is not None),
                'should_aggregate': self.should_aggregate(),
                'last_aggregation': self.last_aggregation.isoformat() if self.last_aggregation else None
            }
        }
    
    def save_global_model(self):
        """Save the global model to disk."""
        os.makedirs(os.path.dirname(self.global_model_path), exist_ok=True)
        with open(self.global_model_path, 'wb') as f:
            pickle.dump(self.global_model, f)
    
    def load_global_model(self):
        """Load the global model from disk."""
        with open(self.global_model_path, 'rb') as f:
            self.global_model = pickle.load(f)
    
    def get_model_parameters(self) -> Dict[str, Any]:
        """Get current global model parameters."""
        return self.global_model.copy()


class FederatedLearningManager:
    """Manager class for coordinating federated learning across the system."""
    
    def __init__(self):
        self.aggregator = FederatedAggregator()
        self.auto_aggregation_thread = None
        self.auto_aggregation_running = False
    
    def start_auto_aggregation(self):
        """Start automatic model aggregation in background thread."""
        if self.auto_aggregation_running:
            logger.warning("Auto-aggregation already running")
            return
        
        self.auto_aggregation_running = True
        self.auto_aggregation_thread = threading.Thread(target=self._auto_aggregation_loop, daemon=True)
        self.auto_aggregation_thread.start()
        
        logger.info("Started automatic federated learning aggregation")
    
    def stop_auto_aggregation(self):
        """Stop automatic model aggregation."""
        self.auto_aggregation_running = False
        if self.auto_aggregation_thread:
            self.auto_aggregation_thread.join(timeout=5)
        
        logger.info("Stopped automatic federated learning aggregation")
    
    def _auto_aggregation_loop(self):
        """Background loop for automatic model aggregation."""
        while self.auto_aggregation_running:
            try:
                if self.aggregator.should_aggregate():
                    result = self.aggregator.aggregate_models()
                    if result['status'] == 'completed':
                        self.aggregator.last_aggregation = datetime.utcnow()
                        logger.info(f"Auto-aggregation completed: {result}")
                
                # Sleep for 5 minutes before checking again
                time.sleep(300)
                
            except Exception as e:
                logger.error(f"Error in auto-aggregation loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def register_node(self, node_id: str) -> FederatedNode:
        """Register a new federated learning node."""
        return self.aggregator.register_node(node_id)
    
    def get_node(self, node_id: str) -> Optional[FederatedNode]:
        """Get a registered federated learning node."""
        return self.aggregator.nodes.get(node_id)
    
    def aggregate_now(self) -> Dict[str, Any]:
        """Manually trigger model aggregation."""
        return self.aggregator.aggregate_models()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get the complete federated learning system status."""
        return self.aggregator.get_global_model_status()
    
    def get_global_model_parameters(self) -> Dict[str, Any]:
        """Get current global model parameters."""
        return self.aggregator.get_model_parameters()
