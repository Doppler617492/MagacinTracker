import numpy as np
import pickle
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)


class SimpleNeuralNetwork:
    """
    Simple neural network implementation for worker performance prediction.
    This is a lightweight alternative to PyTorch/TensorFlow for demonstration.
    """
    
    def __init__(self, input_size: int = 8, hidden_size: int = 16, output_size: int = 1):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        # Initialize weights with Xavier initialization
        self.W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
        self.b1 = np.zeros((1, hidden_size))
        self.W2 = np.random.randn(hidden_size, hidden_size) * np.sqrt(2.0 / hidden_size)
        self.b2 = np.zeros((1, hidden_size))
        self.W3 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
        self.b3 = np.zeros((1, output_size))
        
        self.training_history = []
        self.is_trained = False
        self.last_trained = None
    
    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function."""
        return np.maximum(0, x)
    
    def relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """ReLU derivative."""
        return (x > 0).astype(float)
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function."""
        return 1 / (1 + np.exp(-np.clip(x, -250, 250)))
    
    def sigmoid_derivative(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid derivative."""
        s = self.sigmoid(x)
        return s * (1 - s)
    
    def forward(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Forward propagation."""
        # Layer 1
        z1 = np.dot(X, self.W1) + self.b1
        a1 = self.relu(z1)
        
        # Layer 2
        z2 = np.dot(a1, self.W2) + self.b2
        a2 = self.relu(z2)
        
        # Output layer
        z3 = np.dot(a2, self.W3) + self.b3
        a3 = self.sigmoid(z3)
        
        return a3, a2, a1, z1
    
    def backward(self, X: np.ndarray, y: np.ndarray, a3: np.ndarray, a2: np.ndarray, a1: np.ndarray, z1: np.ndarray) -> Dict[str, np.ndarray]:
        """Backward propagation."""
        m = X.shape[0]
        
        # Output layer gradients
        dz3 = a3 - y
        dW3 = (1/m) * np.dot(a2.T, dz3)
        db3 = (1/m) * np.sum(dz3, axis=0, keepdims=True)
        
        # Hidden layer 2 gradients
        da2 = np.dot(dz3, self.W3.T)
        dz2 = da2 * self.relu_derivative(a2)
        dW2 = (1/m) * np.dot(a1.T, dz2)
        db2 = (1/m) * np.sum(dz2, axis=0, keepdims=True)
        
        # Hidden layer 1 gradients
        da1 = np.dot(dz2, self.W2.T)
        dz1 = da1 * self.relu_derivative(z1)
        dW1 = (1/m) * np.dot(X.T, dz1)
        db1 = (1/m) * np.sum(dz1, axis=0, keepdims=True)
        
        return {
            'dW1': dW1, 'db1': db1,
            'dW2': dW2, 'db2': db2,
            'dW3': dW3, 'db3': db3
        }
    
    def update_weights(self, gradients: Dict[str, np.ndarray], learning_rate: float):
        """Update weights using gradients."""
        self.W1 -= learning_rate * gradients['dW1']
        self.b1 -= learning_rate * gradients['db1']
        self.W2 -= learning_rate * gradients['dW2']
        self.b2 -= learning_rate * gradients['db2']
        self.W3 -= learning_rate * gradients['dW3']
        self.b3 -= learning_rate * gradients['db3']
    
    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute mean squared error loss."""
        m = y_true.shape[0]
        loss = (1/(2*m)) * np.sum(np.square(y_pred - y_true))
        return loss
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 100, learning_rate: float = 0.001, verbose: bool = True) -> Dict[str, List[float]]:
        """Train the neural network."""
        logger.info(f"Starting neural network training with {epochs} epochs")
        
        losses = []
        accuracies = []
        
        for epoch in range(epochs):
            # Forward propagation
            a3, a2, a1, z1 = self.forward(X)
            
            # Compute loss
            loss = self.compute_loss(a3, y)
            losses.append(loss)
            
            # Compute accuracy (for regression, use R²)
            accuracy = self.compute_r_squared(a3, y)
            accuracies.append(accuracy)
            
            # Backward propagation
            gradients = self.backward(X, y, a3, a2, a1, z1)
            
            # Update weights
            self.update_weights(gradients, learning_rate)
            
            if verbose and epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Loss = {loss:.4f}, R² = {accuracy:.4f}")
        
        self.is_trained = True
        self.last_trained = datetime.utcnow()
        
        training_history = {
            'losses': losses,
            'accuracies': accuracies,
            'epochs': epochs,
            'final_loss': losses[-1],
            'final_accuracy': accuracies[-1]
        }
        
        self.training_history.append(training_history)
        logger.info(f"Training completed. Final loss: {losses[-1]:.4f}, Final R²: {accuracies[-1]:.4f}")
        
        return training_history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        a3, _, _, _ = self.forward(X)
        return a3
    
    def compute_r_squared(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute R² score for regression."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0, min(1, r_squared))
    
    def save_model(self, filepath: str):
        """Save the trained model."""
        model_data = {
            'W1': self.W1,
            'b1': self.b1,
            'W2': self.W2,
            'b2': self.b2,
            'W3': self.W3,
            'b3': self.b3,
            'input_size': self.input_size,
            'hidden_size': self.hidden_size,
            'output_size': self.output_size,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'training_history': self.training_history
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.W1 = model_data['W1']
        self.b1 = model_data['b1']
        self.W2 = model_data['W2']
        self.b2 = model_data['b2']
        self.W3 = model_data['W3']
        self.b3 = model_data['b3']
        self.input_size = model_data['input_size']
        self.hidden_size = model_data['hidden_size']
        self.output_size = model_data['output_size']
        self.is_trained = model_data['is_trained']
        self.last_trained = model_data['last_trained']
        self.training_history = model_data.get('training_history', [])
        
        logger.info(f"Model loaded from {filepath}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and statistics."""
        return {
            'architecture': {
                'input_size': self.input_size,
                'hidden_size': self.hidden_size,
                'output_size': self.output_size,
                'total_parameters': self.input_size * self.hidden_size + self.hidden_size * self.hidden_size + self.hidden_size * self.output_size
            },
            'training_status': {
                'is_trained': self.is_trained,
                'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                'training_sessions': len(self.training_history)
            },
            'performance': {
                'final_loss': self.training_history[-1]['final_loss'] if self.training_history else None,
                'final_accuracy': self.training_history[-1]['final_accuracy'] if self.training_history else None,
                'best_accuracy': max([h['final_accuracy'] for h in self.training_history]) if self.training_history else None
            }
        }


class WorkerPerformancePredictor:
    """Wrapper class for worker performance prediction using neural networks."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = SimpleNeuralNetwork()
        self.model_path = model_path or "./models/worker_performance.pkl"
        
        if os.path.exists(self.model_path):
            try:
                self.model.load_model(self.model_path)
                logger.info("Loaded existing worker performance model")
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")
    
    def prepare_training_data(self, historical_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from historical worker performance data."""
        X = []
        y = []
        
        for record in historical_data:
            # Features: [current_tasks, completed_tasks_today, avg_completion_time, efficiency_score, 
            #           idle_time_percentage, day_of_week, hour_of_day, store_load_index]
            features = [
                record.get('current_tasks', 0) / 10.0,  # Normalize
                record.get('completed_tasks_today', 0) / 50.0,  # Normalize
                record.get('avg_completion_time', 5.0) / 10.0,  # Normalize
                record.get('efficiency_score', 0.5),
                record.get('idle_time_percentage', 0.2),
                record.get('day_of_week', 1) / 7.0,  # Normalize
                record.get('hour_of_day', 12) / 24.0,  # Normalize
                record.get('store_load_index', 0.5)
            ]
            
            # Target: expected performance (0-1 scale)
            target = record.get('performance_score', 0.5)
            
            X.append(features)
            y.append([target])
        
        return np.array(X), np.array(y)
    
    def train_model(self, historical_data: List[Dict[str, Any]], epochs: int = 100) -> Dict[str, Any]:
        """Train the worker performance prediction model."""
        logger.info(f"Training worker performance model with {len(historical_data)} samples")
        
        X, y = self.prepare_training_data(historical_data)
        
        if len(X) == 0:
            raise ValueError("No training data provided")
        
        training_history = self.model.train(X, y, epochs=epochs)
        
        # Save the trained model
        self.model.save_model(self.model_path)
        
        return training_history
    
    def predict_performance(self, worker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict worker performance based on current conditions."""
        if not self.model.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare input features
        features = np.array([[
            worker_data.get('current_tasks', 0) / 10.0,
            worker_data.get('completed_tasks_today', 0) / 50.0,
            worker_data.get('avg_completion_time', 5.0) / 10.0,
            worker_data.get('efficiency_score', 0.5),
            worker_data.get('idle_time_percentage', 0.2),
            worker_data.get('day_of_week', 1) / 7.0,
            worker_data.get('hour_of_day', 12) / 24.0,
            worker_data.get('store_load_index', 0.5)
        ]])
        
        # Make prediction
        prediction = self.model.predict(features)[0][0]
        
        return {
            'predicted_performance': float(prediction),
            'confidence': 0.85,  # Mock confidence score
            'model_info': self.model.get_model_info()
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and performance metrics."""
        return self.model.get_model_info()
