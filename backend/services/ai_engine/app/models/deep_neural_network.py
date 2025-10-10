import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
import math

logger = logging.getLogger(__name__)


class DeepNeuralNetwork:
    """
    Deep Neural Network implementation for complex pattern recognition.
    6-layer architecture optimized for warehouse operations analysis.
    """
    
    def __init__(self, input_size: int = 12, hidden_layers: List[int] = [64, 128, 64, 32, 8], output_size: int = 1):
        self.input_size = input_size
        self.hidden_layers = hidden_layers
        self.output_size = output_size
        self.layer_sizes = [input_size] + hidden_layers + [output_size]
        
        # Initialize weights and biases with Xavier initialization
        self.weights = []
        self.biases = []
        
        for i in range(len(self.layer_sizes) - 1):
            # Xavier initialization
            limit = np.sqrt(6.0 / (self.layer_sizes[i] + self.layer_sizes[i + 1]))
            W = np.random.uniform(-limit, limit, (self.layer_sizes[i], self.layer_sizes[i + 1]))
            b = np.zeros((1, self.layer_sizes[i + 1]))
            
            self.weights.append(W)
            self.biases.append(b)
        
        # Adam optimizer parameters
        self.beta1 = 0.9
        self.beta2 = 0.999
        self.epsilon = 1e-8
        self.learning_rate = 0.001
        
        # Adam optimizer state
        self.m_weights = [np.zeros_like(w) for w in self.weights]
        self.v_weights = [np.zeros_like(w) for w in self.weights]
        self.m_biases = [np.zeros_like(b) for b in self.biases]
        self.v_biases = [np.zeros_like(b) for b in self.biases]
        self.t = 0
        
        # Training history
        self.training_history = []
        self.is_trained = False
        self.last_trained = None
        self.best_accuracy = 0.0
    
    def relu(self, x: np.ndarray) -> np.ndarray:
        """ReLU activation function with leaky variant for stability."""
        return np.maximum(0.01 * x, x)
    
    def relu_derivative(self, x: np.ndarray) -> np.ndarray:
        """Leaky ReLU derivative."""
        return np.where(x > 0, 1.0, 0.01)
    
    def sigmoid(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid activation function with clipping for numerical stability."""
        return 1 / (1 + np.exp(-np.clip(x, -250, 250)))
    
    def sigmoid_derivative(self, x: np.ndarray) -> np.ndarray:
        """Sigmoid derivative."""
        s = self.sigmoid(x)
        return s * (1 - s)
    
    def dropout(self, x: np.ndarray, keep_prob: float = 0.8, training: bool = True) -> np.ndarray:
        """Dropout regularization."""
        if not training:
            return x
        
        mask = np.random.binomial(1, keep_prob, x.shape) / keep_prob
        return x * mask
    
    def batch_normalization(self, x: np.ndarray, gamma: float = 1.0, beta: float = 0.0, 
                          running_mean: float = 0.0, running_var: float = 1.0, 
                          training: bool = True) -> np.ndarray:
        """Batch normalization for training stability."""
        if training:
            batch_mean = np.mean(x, axis=0)
            batch_var = np.var(x, axis=0)
            
            # Update running statistics
            running_mean = 0.9 * running_mean + 0.1 * batch_mean
            running_var = 0.9 * running_var + 0.1 * batch_var
            
            # Normalize
            x_norm = (x - batch_mean) / np.sqrt(batch_var + self.epsilon)
        else:
            x_norm = (x - running_mean) / np.sqrt(running_var + self.epsilon)
        
        return gamma * x_norm + beta
    
    def forward(self, X: np.ndarray, training: bool = True) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Forward propagation through all layers."""
        activations = [X]
        z_values = []
        
        current_input = X
        
        for i in range(len(self.weights)):
            # Linear transformation
            z = np.dot(current_input, self.weights[i]) + self.biases[i]
            z_values.append(z)
            
            # Apply activation function
            if i == len(self.weights) - 1:  # Output layer
                a = self.sigmoid(z)
            else:  # Hidden layers
                a = self.relu(z)
                # Apply batch normalization
                a = self.batch_normalization(a, training=training)
                # Apply dropout
                a = self.dropout(a, keep_prob=0.8, training=training)
            
            activations.append(a)
            current_input = a
        
        return activations, z_values
    
    def backward(self, X: np.ndarray, y: np.ndarray, activations: List[np.ndarray], 
                z_values: List[np.ndarray]) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Backward propagation with gradient computation."""
        m = X.shape[0]
        
        # Initialize gradients
        dW = [np.zeros_like(w) for w in self.weights]
        db = [np.zeros_like(b) for b in self.biases]
        
        # Output layer gradient
        dz = activations[-1] - y
        dW[-1] = (1/m) * np.dot(activations[-2].T, dz)
        db[-1] = (1/m) * np.sum(dz, axis=0, keepdims=True)
        
        # Hidden layers gradients (backpropagate)
        for i in range(len(self.weights) - 2, -1, -1):
            # Gradient w.r.t. activation
            da = np.dot(dz, self.weights[i + 1].T)
            
            # Gradient w.r.t. z (before activation)
            dz = da * self.relu_derivative(z_values[i])
            
            # Gradients w.r.t. weights and biases
            dW[i] = (1/m) * np.dot(activations[i].T, dz)
            db[i] = (1/m) * np.sum(dz, axis=0, keepdims=True)
        
        return dW, db
    
    def adam_update(self, dW: List[np.ndarray], db: List[np.ndarray]):
        """Adam optimizer update step."""
        self.t += 1
        
        for i in range(len(self.weights)):
            # Update weights
            self.m_weights[i] = self.beta1 * self.m_weights[i] + (1 - self.beta1) * dW[i]
            self.v_weights[i] = self.beta2 * self.v_weights[i] + (1 - self.beta2) * (dW[i] ** 2)
            
            m_hat = self.m_weights[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v_weights[i] / (1 - self.beta2 ** self.t)
            
            self.weights[i] -= self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)
            
            # Update biases
            self.m_biases[i] = self.beta1 * self.m_biases[i] + (1 - self.beta1) * db[i]
            self.v_biases[i] = self.beta2 * self.v_biases[i] + (1 - self.beta2) * (db[i] ** 2)
            
            m_hat = self.m_biases[i] / (1 - self.beta1 ** self.t)
            v_hat = self.v_biases[i] / (1 - self.beta2 ** self.t)
            
            self.biases[i] -= self.learning_rate * m_hat / (np.sqrt(v_hat) + self.epsilon)
    
    def compute_loss(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute mean squared error loss with L2 regularization."""
        m = y_true.shape[0]
        
        # MSE loss
        mse_loss = (1/(2*m)) * np.sum(np.square(y_pred - y_true))
        
        # L2 regularization
        l2_reg = 0.001 * sum([np.sum(w ** 2) for w in self.weights])
        
        return mse_loss + l2_reg
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 200, batch_size: int = 32, 
              validation_split: float = 0.2, verbose: bool = True) -> Dict[str, Any]:
        """Train the deep neural network with advanced techniques."""
        logger.info(f"Starting deep neural network training with {epochs} epochs")
        
        # Split data into training and validation
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        train_losses = []
        val_losses = []
        train_accuracies = []
        val_accuracies = []
        
        best_val_accuracy = 0.0
        patience = 20
        patience_counter = 0
        
        for epoch in range(epochs):
            # Shuffle training data
            indices = np.random.permutation(len(X_train))
            X_train_shuffled = X_train[indices]
            y_train_shuffled = y_train[indices]
            
            epoch_train_loss = 0.0
            epoch_train_accuracy = 0.0
            
            # Mini-batch training
            for i in range(0, len(X_train_shuffled), batch_size):
                batch_X = X_train_shuffled[i:i+batch_size]
                batch_y = y_train_shuffled[i:i+batch_size]
                
                # Forward pass
                activations, z_values = self.forward(batch_X, training=True)
                
                # Compute loss
                batch_loss = self.compute_loss(activations[-1], batch_y)
                epoch_train_loss += batch_loss
                
                # Compute accuracy
                batch_accuracy = self.compute_r_squared(activations[-1], batch_y)
                epoch_train_accuracy += batch_accuracy
                
                # Backward pass
                dW, db = self.backward(batch_X, batch_y, activations, z_values)
                
                # Adam update
                self.adam_update(dW, db)
            
            # Average training metrics
            avg_train_loss = epoch_train_loss / (len(X_train_shuffled) // batch_size)
            avg_train_accuracy = epoch_train_accuracy / (len(X_train_shuffled) // batch_size)
            
            # Validation
            val_activations, _ = self.forward(X_val, training=False)
            val_loss = self.compute_loss(val_activations[-1], y_val)
            val_accuracy = self.compute_r_squared(val_activations[-1], y_val)
            
            train_losses.append(avg_train_loss)
            val_losses.append(val_loss)
            train_accuracies.append(avg_train_accuracy)
            val_accuracies.append(val_accuracy)
            
            # Early stopping
            if val_accuracy > best_val_accuracy:
                best_val_accuracy = val_accuracy
                patience_counter = 0
            else:
                patience_counter += 1
            
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break
            
            if verbose and epoch % 20 == 0:
                logger.info(f"Epoch {epoch}: Train Loss = {avg_train_loss:.4f}, Val Loss = {val_loss:.4f}, "
                           f"Train Acc = {avg_train_accuracy:.4f}, Val Acc = {val_accuracy:.4f}")
        
        self.is_trained = True
        self.last_trained = datetime.utcnow()
        self.best_accuracy = best_val_accuracy
        
        training_history = {
            'epochs': epoch + 1,
            'train_losses': train_losses,
            'val_losses': val_losses,
            'train_accuracies': train_accuracies,
            'val_accuracies': val_accuracies,
            'final_train_loss': train_losses[-1],
            'final_val_loss': val_losses[-1],
            'final_train_accuracy': train_accuracies[-1],
            'final_val_accuracy': val_accuracies[-1],
            'best_val_accuracy': best_val_accuracy,
            'early_stopped': patience_counter >= patience
        }
        
        self.training_history.append(training_history)
        logger.info(f"Deep neural network training completed. Best validation accuracy: {best_val_accuracy:.4f}")
        
        return training_history
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions using the trained model."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        activations, _ = self.forward(X, training=False)
        return activations[-1]
    
    def compute_r_squared(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute R² score for regression."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0, min(1, r_squared))
    
    def get_feature_importance(self, X: np.ndarray, feature_names: List[str]) -> Dict[str, float]:
        """Compute feature importance using permutation importance."""
        if not self.is_trained:
            raise ValueError("Model must be trained before computing feature importance")
        
        # Baseline prediction
        baseline_pred = self.predict(X)
        baseline_mse = np.mean((baseline_pred - np.mean(baseline_pred)) ** 2)
        
        feature_importance = {}
        
        for i, feature_name in enumerate(feature_names):
            # Permute feature
            X_permuted = X.copy()
            np.random.shuffle(X_permuted[:, i])
            
            # Predict with permuted feature
            permuted_pred = self.predict(X_permuted)
            permuted_mse = np.mean((permuted_pred - np.mean(permuted_pred)) ** 2)
            
            # Importance is the increase in MSE
            importance = permuted_mse - baseline_mse
            feature_importance[feature_name] = float(importance)
        
        return feature_importance
    
    def save_model(self, filepath: str):
        """Save the trained deep neural network model."""
        model_data = {
            'weights': self.weights,
            'biases': self.biases,
            'layer_sizes': self.layer_sizes,
            'input_size': self.input_size,
            'hidden_layers': self.hidden_layers,
            'output_size': self.output_size,
            'learning_rate': self.learning_rate,
            'beta1': self.beta1,
            'beta2': self.beta2,
            'epsilon': self.epsilon,
            'm_weights': self.m_weights,
            'v_weights': self.v_weights,
            'm_biases': self.m_biases,
            'v_biases': self.v_biases,
            't': self.t,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'best_accuracy': self.best_accuracy,
            'training_history': self.training_history
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Deep neural network model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained deep neural network model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.weights = model_data['weights']
        self.biases = model_data['biases']
        self.layer_sizes = model_data['layer_sizes']
        self.input_size = model_data['input_size']
        self.hidden_layers = model_data['hidden_layers']
        self.output_size = model_data['output_size']
        self.learning_rate = model_data['learning_rate']
        self.beta1 = model_data['beta1']
        self.beta2 = model_data['beta2']
        self.epsilon = model_data['epsilon']
        self.m_weights = model_data['m_weights']
        self.v_weights = model_data['v_weights']
        self.m_biases = model_data['m_biases']
        self.v_biases = model_data['v_biases']
        self.t = model_data['t']
        self.is_trained = model_data['is_trained']
        self.last_trained = model_data['last_trained']
        self.best_accuracy = model_data['best_accuracy']
        self.training_history = model_data['training_history']
        
        logger.info(f"Deep neural network model loaded from {filepath}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and performance metrics."""
        return {
            'architecture': {
                'input_size': self.input_size,
                'hidden_layers': self.hidden_layers,
                'output_size': self.output_size,
                'total_parameters': sum(w.size + b.size for w, b in zip(self.weights, self.biases)),
                'total_layers': len(self.layer_sizes) - 1
            },
            'training_status': {
                'is_trained': self.is_trained,
                'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                'training_sessions': len(self.training_history),
                'total_epochs': sum(h.get('epochs', 0) for h in self.training_history)
            },
            'performance': {
                'best_accuracy': self.best_accuracy,
                'final_accuracy': self.training_history[-1]['final_val_accuracy'] if self.training_history else None,
                'final_loss': self.training_history[-1]['final_val_loss'] if self.training_history else None,
                'early_stopped': self.training_history[-1]['early_stopped'] if self.training_history else False
            },
            'optimizer': {
                'type': 'Adam',
                'learning_rate': self.learning_rate,
                'beta1': self.beta1,
                'beta2': self.beta2,
                'epsilon': self.epsilon,
                'update_steps': self.t
            }
        }


class GlobalPerformancePredictor:
    """Advanced predictor using deep neural networks for global warehouse optimization."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.model = DeepNeuralNetwork()
        self.model_path = model_path or "./models/global_performance_dnn.pkl"
        self.feature_names = [
            'current_tasks', 'completed_tasks_today', 'avg_completion_time',
            'efficiency_score', 'idle_time_percentage', 'day_of_week',
            'hour_of_day', 'store_load_index', 'seasonality_factor',
            'product_complexity', 'worker_experience', 'team_size'
        ]
        
        if os.path.exists(self.model_path):
            try:
                self.model.load_model(self.model_path)
                logger.info("Loaded existing global performance DNN model")
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")
    
    def prepare_enhanced_training_data(self, historical_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare enhanced training data with additional features."""
        X = []
        y = []
        
        for record in historical_data:
            # Enhanced feature set
            features = [
                record.get('current_tasks', 0) / 15.0,  # Normalize
                record.get('completed_tasks_today', 0) / 60.0,  # Normalize
                record.get('avg_completion_time', 5.0) / 15.0,  # Normalize
                record.get('efficiency_score', 0.5),
                record.get('idle_time_percentage', 0.2),
                record.get('day_of_week', 1) / 7.0,  # Normalize
                record.get('hour_of_day', 12) / 24.0,  # Normalize
                record.get('store_load_index', 0.5),
                record.get('seasonality_factor', 0.5),  # New feature
                record.get('product_complexity', 0.5),  # New feature
                record.get('worker_experience', 0.5),   # New feature
                record.get('team_size', 1) / 10.0       # New feature
            ]
            
            # Target: enhanced performance score
            target = record.get('performance_score', 0.5)
            
            X.append(features)
            y.append([target])
        
        return np.array(X), np.array(y)
    
    def train_model(self, historical_data: List[Dict[str, Any]], epochs: int = 200) -> Dict[str, Any]:
        """Train the global performance prediction model."""
        logger.info(f"Training global performance DNN with {len(historical_data)} samples")
        
        X, y = self.prepare_enhanced_training_data(historical_data)
        
        if len(X) == 0:
            raise ValueError("No training data provided")
        
        training_history = self.model.train(X, y, epochs=epochs)
        
        # Save the trained model
        self.model.save_model(self.model_path)
        
        return training_history
    
    def predict_performance(self, worker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict worker performance using the deep neural network."""
        if not self.model.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare enhanced input features
        features = np.array([[
            worker_data.get('current_tasks', 0) / 15.0,
            worker_data.get('completed_tasks_today', 0) / 60.0,
            worker_data.get('avg_completion_time', 5.0) / 15.0,
            worker_data.get('efficiency_score', 0.5),
            worker_data.get('idle_time_percentage', 0.2),
            worker_data.get('day_of_week', 1) / 7.0,
            worker_data.get('hour_of_day', 12) / 24.0,
            worker_data.get('store_load_index', 0.5),
            worker_data.get('seasonality_factor', 0.5),
            worker_data.get('product_complexity', 0.5),
            worker_data.get('worker_experience', 0.5),
            worker_data.get('team_size', 1) / 10.0
        ]])
        
        # Make prediction
        prediction = self.model.predict(features)[0][0]
        
        # Get feature importance
        feature_importance = self.model.get_feature_importance(features, self.feature_names)
        
        return {
            'predicted_performance': float(prediction),
            'confidence': min(0.95, 0.7 + self.model.best_accuracy * 0.3),
            'feature_importance': feature_importance,
            'model_info': self.model.get_model_info()
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and performance metrics."""
        return self.model.get_model_info()
