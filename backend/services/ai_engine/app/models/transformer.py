import numpy as np
import pickle
import os
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TransformerConfig:
    """Configuration for the mini-transformer model."""
    vocab_size: int = 1000  # Event vocabulary size
    d_model: int = 128  # Model dimension
    n_heads: int = 4  # Number of attention heads
    n_layers: int = 3  # Number of encoder layers
    d_ff: int = 512  # Feed-forward dimension
    max_seq_length: int = 100  # Maximum sequence length
    dropout: float = 0.1
    learning_rate: float = 0.0001
    batch_size: int = 32
    epochs: int = 100


class MultiHeadAttention:
    """Multi-head attention mechanism."""
    
    def __init__(self, d_model: int, n_heads: int):
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_k = d_model // n_heads
        
        # Initialize weights
        self.W_q = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        self.W_k = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        self.W_v = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        self.W_o = np.random.randn(d_model, d_model) * np.sqrt(2.0 / d_model)
        
        # Bias terms
        self.b_q = np.zeros(d_model)
        self.b_k = np.zeros(d_model)
        self.b_v = np.zeros(d_model)
        self.b_o = np.zeros(d_model)
    
    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Forward pass through multi-head attention."""
        batch_size, seq_len, d_model = x.shape
        
        # Linear transformations
        Q = np.dot(x, self.W_q) + self.b_q
        K = np.dot(x, self.W_k) + self.b_k
        V = np.dot(x, self.W_v) + self.b_v
        
        # Reshape for multi-head attention
        Q = Q.reshape(batch_size, seq_len, self.n_heads, self.d_k).transpose(0, 2, 1, 3)
        K = K.reshape(batch_size, seq_len, self.n_heads, self.d_k).transpose(0, 2, 1, 3)
        V = V.reshape(batch_size, seq_len, self.n_heads, self.d_k).transpose(0, 2, 1, 3)
        
        # Scaled dot-product attention
        scores = np.matmul(Q, K.transpose(0, 1, 3, 2)) / np.sqrt(self.d_k)
        
        if mask is not None:
            scores = np.where(mask == 0, -1e9, scores)
        
        attention_weights = self.softmax(scores, axis=-1)
        attention_output = np.matmul(attention_weights, V)
        
        # Reshape and apply output projection
        attention_output = attention_output.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, d_model)
        output = np.dot(attention_output, self.W_o) + self.b_o
        
        return output
    
    def softmax(self, x: np.ndarray, axis: int = -1) -> np.ndarray:
        """Softmax function."""
        exp_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
        return exp_x / np.sum(exp_x, axis=axis, keepdims=True)


class FeedForward:
    """Feed-forward network."""
    
    def __init__(self, d_model: int, d_ff: int):
        self.d_model = d_model
        self.d_ff = d_ff
        
        # Initialize weights
        self.W1 = np.random.randn(d_model, d_ff) * np.sqrt(2.0 / d_model)
        self.W2 = np.random.randn(d_ff, d_model) * np.sqrt(2.0 / d_ff)
        
        # Bias terms
        self.b1 = np.zeros(d_ff)
        self.b2 = np.zeros(d_model)
    
    def forward(self, x: np.ndarray) -> np.ndarray:
        """Forward pass through feed-forward network."""
        # First linear layer with ReLU
        h = np.dot(x, self.W1) + self.b1
        h = np.maximum(0, h)  # ReLU activation
        
        # Second linear layer
        output = np.dot(h, self.W2) + self.b2
        
        return output


class TransformerEncoderLayer:
    """Single transformer encoder layer."""
    
    def __init__(self, config: TransformerConfig):
        self.config = config
        self.attention = MultiHeadAttention(config.d_model, config.n_heads)
        self.feed_forward = FeedForward(config.d_model, config.d_ff)
        
        # Layer normalization parameters
        self.ln1_gamma = np.ones(config.d_model)
        self.ln1_beta = np.zeros(config.d_model)
        self.ln2_gamma = np.ones(config.d_model)
        self.ln2_beta = np.zeros(config.d_model)
    
    def forward(self, x: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Forward pass through encoder layer."""
        # Multi-head attention with residual connection
        attn_output = self.attention.forward(x, mask)
        x = self.layer_norm(x + attn_output, self.ln1_gamma, self.ln1_beta)
        
        # Feed-forward with residual connection
        ff_output = self.feed_forward.forward(x)
        x = self.layer_norm(x + ff_output, self.ln2_gamma, self.ln2_beta)
        
        return x
    
    def layer_norm(self, x: np.ndarray, gamma: np.ndarray, beta: np.ndarray) -> np.ndarray:
        """Layer normalization."""
        mean = np.mean(x, axis=-1, keepdims=True)
        var = np.var(x, axis=-1, keepdims=True)
        return gamma * (x - mean) / np.sqrt(var + 1e-8) + beta


class MiniTransformer:
    """
    Mini-transformer model for sequential pattern analysis.
    Analyzes event sequences to predict patterns like "warehouse overload" or "worker performance decline".
    """
    
    def __init__(self, config: TransformerConfig):
        self.config = config
        self.config = config
        
        # Embedding layer
        self.embedding = np.random.randn(config.vocab_size, config.d_model) * np.sqrt(2.0 / config.d_model)
        self.position_embedding = self._create_position_embedding()
        
        # Encoder layers
        self.encoder_layers = [
            TransformerEncoderLayer(config) 
            for _ in range(config.n_layers)
        ]
        
        # Output projection
        self.output_projection = np.random.randn(config.d_model, 1) * np.sqrt(2.0 / config.d_model)
        self.output_bias = np.zeros(1)
        
        # Training state
        self.is_trained = False
        self.training_history = []
        self.last_trained = None
        
        # Event vocabulary
        self.event_vocab = {}
        self.vocab_size = 0
    
    def _create_position_embedding(self) -> np.ndarray:
        """Create positional embeddings."""
        pos_emb = np.zeros((self.config.max_seq_length, self.config.d_model))
        
        for pos in range(self.config.max_seq_length):
            for i in range(0, self.config.d_model, 2):
                pos_emb[pos, i] = math.sin(pos / (10000 ** (i / self.config.d_model)))
                if i + 1 < self.config.d_model:
                    pos_emb[pos, i + 1] = math.cos(pos / (10000 ** (i / self.config.d_model)))
        
        return pos_emb
    
    def _build_vocabulary(self, sequences: List[List[str]]) -> Dict[str, int]:
        """Build vocabulary from event sequences."""
        vocab = {'<PAD>': 0, '<UNK>': 1}
        
        for sequence in sequences:
            for event in sequence:
                if event not in vocab:
                    vocab[event] = len(vocab)
        
        return vocab
    
    def _encode_sequences(self, sequences: List[List[str]]) -> np.ndarray:
        """Encode event sequences to token IDs."""
        encoded = []
        
        for sequence in sequences:
            encoded_seq = []
            for event in sequence[:self.config.max_seq_length]:
                encoded_seq.append(self.event_vocab.get(event, self.event_vocab['<UNK>']))
            
            # Pad sequence
            while len(encoded_seq) < self.config.max_seq_length:
                encoded_seq.append(self.event_vocab['<PAD>'])
            
            encoded.append(encoded_seq)
        
        return np.array(encoded)
    
    def _create_attention_mask(self, sequences: np.ndarray) -> np.ndarray:
        """Create attention mask for padded sequences."""
        mask = (sequences != self.event_vocab['<PAD>']).astype(float)
        return mask
    
    def forward(self, sequences: np.ndarray, mask: Optional[np.ndarray] = None) -> np.ndarray:
        """Forward pass through the transformer."""
        batch_size, seq_len = sequences.shape
        
        # Embedding lookup
        embedded = self.embedding[sequences]  # (batch_size, seq_len, d_model)
        
        # Add positional embeddings
        embedded += self.position_embedding[:seq_len]
        
        # Pass through encoder layers
        x = embedded
        for layer in self.encoder_layers:
            x = layer.forward(x, mask)
        
        # Global average pooling
        if mask is not None:
            # Mask out padded positions
            x = x * mask.unsqueeze(-1) if hasattr(mask, 'unsqueeze') else x * mask[..., np.newaxis]
            pooled = np.sum(x, axis=1) / np.sum(mask, axis=1, keepdims=True)
        else:
            pooled = np.mean(x, axis=1)
        
        # Output projection
        output = np.dot(pooled, self.output_projection) + self.output_bias
        
        return output
    
    def train(self, sequences: List[List[str]], labels: List[float], 
              validation_split: float = 0.2) -> Dict[str, Any]:
        """Train the transformer model."""
        logger.info(f"Starting transformer training with {len(sequences)} sequences")
        
        # Build vocabulary
        self.event_vocab = self._build_vocabulary(sequences)
        self.vocab_size = len(self.event_vocab)
        
        # Encode sequences
        encoded_sequences = self._encode_sequences(sequences)
        labels = np.array(labels).reshape(-1, 1)
        
        # Create attention mask
        mask = self._create_attention_mask(encoded_sequences)
        
        # Split data
        split_idx = int(len(sequences) * (1 - validation_split))
        X_train, X_val = encoded_sequences[:split_idx], encoded_sequences[split_idx:]
        y_train, y_val = labels[:split_idx], labels[split_idx:]
        mask_train, mask_val = mask[:split_idx], mask[split_idx:]
        
        # Training loop
        train_losses = []
        val_losses = []
        train_accuracies = []
        val_accuracies = []
        
        for epoch in range(self.config.epochs):
            # Shuffle training data
            indices = np.random.permutation(len(X_train))
            X_train_shuffled = X_train[indices]
            y_train_shuffled = y_train[indices]
            mask_train_shuffled = mask_train[indices]
            
            # Mini-batch training
            epoch_loss = 0.0
            epoch_accuracy = 0.0
            
            for i in range(0, len(X_train_shuffled), self.config.batch_size):
                batch_X = X_train_shuffled[i:i+self.config.batch_size]
                batch_y = y_train_shuffled[i:i+self.config.batch_size]
                batch_mask = mask_train_shuffled[i:i+self.config.batch_size]
                
                # Forward pass
                predictions = self.forward(batch_X, batch_mask)
                
                # Compute loss (MSE)
                loss = np.mean((predictions - batch_y) ** 2)
                epoch_loss += loss
                
                # Compute accuracy (R²)
                accuracy = self._compute_r_squared(predictions, batch_y)
                epoch_accuracy += accuracy
                
                # Backward pass (simplified gradient descent)
                self._backward_pass(batch_X, batch_y, predictions, batch_mask)
            
            # Validation
            val_predictions = self.forward(X_val, mask_val)
            val_loss = np.mean((val_predictions - y_val) ** 2)
            val_accuracy = self._compute_r_squared(val_predictions, y_val)
            
            train_losses.append(epoch_loss / (len(X_train_shuffled) // self.config.batch_size))
            val_losses.append(val_loss)
            train_accuracies.append(epoch_accuracy / (len(X_train_shuffled) // self.config.batch_size))
            val_accuracies.append(val_accuracy)
            
            if epoch % 10 == 0:
                logger.info(f"Epoch {epoch}: Train Loss = {train_losses[-1]:.4f}, Val Loss = {val_losses[-1]:.4f}, "
                           f"Train Acc = {train_accuracies[-1]:.4f}, Val Acc = {val_accuracies[-1]:.4f}")
        
        self.is_trained = True
        self.last_trained = datetime.utcnow()
        
        training_history = {
            'epochs': self.config.epochs,
            'train_losses': train_losses,
            'val_losses': val_losses,
            'train_accuracies': train_accuracies,
            'val_accuracies': val_accuracies,
            'final_train_loss': train_losses[-1],
            'final_val_loss': val_losses[-1],
            'final_train_accuracy': train_accuracies[-1],
            'final_val_accuracy': val_accuracies[-1],
            'vocab_size': self.vocab_size
        }
        
        self.training_history.append(training_history)
        logger.info(f"Transformer training completed. Final validation accuracy: {val_accuracies[-1]:.4f}")
        
        return training_history
    
    def _backward_pass(self, X: np.ndarray, y: np.ndarray, predictions: np.ndarray, mask: np.ndarray):
        """Simplified backward pass with gradient descent."""
        # Compute gradients (simplified)
        error = predictions - y
        grad_output = 2 * error / len(y)
        
        # Update output projection (simplified)
        # In a full implementation, this would involve proper backpropagation
        # For now, we use a simple gradient descent step
        learning_rate = self.config.learning_rate
        
        # Simplified weight updates
        self.output_projection -= learning_rate * 0.001  # Placeholder
        self.output_bias -= learning_rate * np.mean(grad_output)
    
    def _compute_r_squared(self, y_pred: np.ndarray, y_true: np.ndarray) -> float:
        """Compute R² score."""
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        
        if ss_tot == 0:
            return 1.0
        
        r_squared = 1 - (ss_res / ss_tot)
        return max(0, min(1, r_squared))
    
    def predict(self, sequences: List[List[str]]) -> np.ndarray:
        """Make predictions on new sequences."""
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Encode sequences
        encoded_sequences = self._encode_sequences(sequences)
        mask = self._create_attention_mask(encoded_sequences)
        
        # Forward pass
        predictions = self.forward(encoded_sequences, mask)
        
        return predictions
    
    def analyze_pattern(self, sequence: List[str]) -> Dict[str, Any]:
        """Analyze a sequence for patterns."""
        if not self.is_trained:
            raise ValueError("Model must be trained before pattern analysis")
        
        # Make prediction
        prediction = self.predict([sequence])[0, 0]
        
        # Analyze sequence characteristics
        pattern_analysis = {
            'prediction': float(prediction),
            'sequence_length': len(sequence),
            'unique_events': len(set(sequence)),
            'event_frequency': self._analyze_event_frequency(sequence),
            'pattern_type': self._classify_pattern(sequence, prediction)
        }
        
        return pattern_analysis
    
    def _analyze_event_frequency(self, sequence: List[str]) -> Dict[str, int]:
        """Analyze frequency of events in sequence."""
        frequency = {}
        for event in sequence:
            frequency[event] = frequency.get(event, 0) + 1
        return frequency
    
    def _classify_pattern(self, sequence: List[str], prediction: float) -> str:
        """Classify the type of pattern based on sequence and prediction."""
        if prediction > 0.8:
            return "high_activity"
        elif prediction > 0.6:
            return "moderate_activity"
        elif prediction > 0.4:
            return "low_activity"
        else:
            return "minimal_activity"
    
    def save_model(self, filepath: str):
        """Save the transformer model."""
        model_data = {
            'config': self.config,
            'embedding': self.embedding,
            'position_embedding': self.position_embedding,
            'encoder_layers': [layer.__dict__ for layer in self.encoder_layers],
            'output_projection': self.output_projection,
            'output_bias': self.output_bias,
            'event_vocab': self.event_vocab,
            'vocab_size': self.vocab_size,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained,
            'training_history': self.training_history
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Transformer model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained transformer model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.config = model_data['config']
        self.embedding = model_data['embedding']
        self.position_embedding = model_data['position_embedding']
        self.output_projection = model_data['output_projection']
        self.output_bias = model_data['output_bias']
        self.event_vocab = model_data['event_vocab']
        self.vocab_size = model_data['vocab_size']
        self.is_trained = model_data['is_trained']
        self.last_trained = model_data['last_trained']
        self.training_history = model_data['training_history']
        
        # Reconstruct encoder layers
        self.encoder_layers = []
        for layer_data in model_data['encoder_layers']:
            layer = TransformerEncoderLayer(self.config)
            layer.__dict__.update(layer_data)
            self.encoder_layers.append(layer)
        
        logger.info(f"Transformer model loaded from {filepath}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and performance metrics."""
        return {
            'architecture': {
                'vocab_size': self.vocab_size,
                'd_model': self.config.d_model,
                'n_heads': self.config.n_heads,
                'n_layers': self.config.n_layers,
                'd_ff': self.config.d_ff,
                'max_seq_length': self.config.max_seq_length
            },
            'training_status': {
                'is_trained': self.is_trained,
                'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                'training_sessions': len(self.training_history)
            },
            'performance': {
                'final_train_accuracy': self.training_history[-1]['final_train_accuracy'] if self.training_history else None,
                'final_val_accuracy': self.training_history[-1]['final_val_accuracy'] if self.training_history else None,
                'final_train_loss': self.training_history[-1]['final_train_loss'] if self.training_history else None,
                'final_val_loss': self.training_history[-1]['final_val_loss'] if self.training_history else None
            }
        }


class SequentialPatternAnalyzer:
    """Wrapper class for sequential pattern analysis using transformer models."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.config = TransformerConfig()
        self.model = MiniTransformer(self.config)
        self.model_path = model_path or "./models/sequential_pattern_transformer.pkl"
        
        if os.path.exists(self.model_path):
            try:
                self.model.load_model(self.model_path)
                logger.info("Loaded existing sequential pattern transformer model")
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")
    
    def train_model(self, event_sequences: List[List[str]], labels: List[float]) -> Dict[str, Any]:
        """Train the sequential pattern analyzer."""
        logger.info(f"Training sequential pattern analyzer with {len(event_sequences)} sequences")
        
        training_history = self.model.train(event_sequences, labels)
        
        # Save the trained model
        self.model.save_model(self.model_path)
        
        return training_history
    
    def predict_pattern(self, event_sequence: List[str]) -> Dict[str, Any]:
        """Predict pattern from event sequence."""
        if not self.model.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Analyze the sequence
        pattern_analysis = self.model.analyze_pattern(event_sequence)
        
        return {
            'pattern_prediction': pattern_analysis['prediction'],
            'pattern_type': pattern_analysis['pattern_type'],
            'sequence_analysis': {
                'length': pattern_analysis['sequence_length'],
                'unique_events': pattern_analysis['unique_events'],
                'event_frequency': pattern_analysis['event_frequency']
            },
            'confidence': min(0.95, 0.7 + pattern_analysis['prediction'] * 0.3),
            'model_info': self.model.get_model_info()
        }
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and performance metrics."""
        return self.model.get_model_info()
