import numpy as np
import pickle
import os
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ActionType(Enum):
    REASSIGN_TASK = "reassign_task"
    ASSIGN_WORKER = "assign_worker"
    REDUCE_LOAD = "reduce_load"
    INCREASE_CAPACITY = "increase_capacity"
    NO_ACTION = "no_action"


class QLearningAgent:
    """
    Q-Learning agent for adaptive task optimization in real-time.
    Learns optimal actions based on warehouse state and rewards.
    """
    
    def __init__(self, state_size: int = 10, action_size: int = 5, learning_rate: float = 0.01, 
                 discount_factor: float = 0.95, epsilon: float = 0.1):
        self.state_size = state_size
        self.action_size = action_size
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon
        
        # Q-table: state -> action -> Q-value
        self.q_table = np.random.uniform(low=-0.1, high=0.1, size=(state_size, action_size))
        
        # Training history
        self.training_history = []
        self.episode_rewards = []
        self.episode_steps = []
        
        # Performance metrics
        self.total_episodes = 0
        self.total_reward = 0.0
        self.best_reward = float('-inf')
        self.is_trained = False
        self.last_trained = None
    
    def state_to_index(self, state: Dict[str, Any]) -> int:
        """Convert warehouse state to Q-table index."""
        # Discretize continuous state variables
        load_balance = min(9, int(state.get('load_balance_variance', 0.5) * 10))
        avg_efficiency = min(9, int(state.get('average_efficiency', 0.5) * 10))
        
        # Combine into single index (simplified)
        state_index = load_balance * 10 + avg_efficiency
        return min(self.state_size - 1, state_index)
    
    def get_action(self, state: Dict[str, Any], training: bool = True) -> Tuple[int, ActionType]:
        """Choose action using epsilon-greedy policy."""
        state_index = self.state_to_index(state)
        
        if training and np.random.random() < self.epsilon:
            # Exploration: random action
            action_index = np.random.randint(0, self.action_size)
        else:
            # Exploitation: best known action
            action_index = np.argmax(self.q_table[state_index])
        
        action_type = list(ActionType)[action_index]
        return action_index, action_type
    
    def update_q_value(self, state: Dict[str, Any], action_index: int, reward: float, 
                      next_state: Dict[str, Any], done: bool = False):
        """Update Q-value using Q-learning algorithm."""
        state_index = self.state_to_index(state)
        next_state_index = self.state_to_index(next_state)
        
        current_q = self.q_table[state_index, action_index]
        
        if done:
            target_q = reward
        else:
            target_q = reward + self.discount_factor * np.max(self.q_table[next_state_index])
        
        # Q-learning update
        self.q_table[state_index, action_index] = current_q + self.learning_rate * (target_q - current_q)
    
    def calculate_reward(self, state: Dict[str, Any], action: ActionType, next_state: Dict[str, Any]) -> float:
        """Calculate reward based on state transition and action taken."""
        reward = 0.0
        
        # Load balance improvement
        load_balance_improvement = state.get('load_balance_variance', 0.5) - next_state.get('load_balance_variance', 0.5)
        reward += load_balance_improvement * 10
        
        # Efficiency improvement
        efficiency_improvement = next_state.get('average_efficiency', 0.5) - state.get('average_efficiency', 0.5)
        reward += efficiency_improvement * 20
        
        # Idle time reduction
        idle_improvement = state.get('average_idle_time', 0.3) - next_state.get('average_idle_time', 0.3)
        reward += idle_improvement * 15
        
        # Action-specific rewards
        if action == ActionType.REASSIGN_TASK:
            reward += 5  # Positive reward for task reassignment
        elif action == ActionType.ASSIGN_WORKER:
            reward += 8  # Higher reward for worker assignment
        elif action == ActionType.NO_ACTION:
            reward -= 1  # Small penalty for inaction
        
        # Penalty for negative changes
        if load_balance_improvement < 0:
            reward -= 5
        if efficiency_improvement < 0:
            reward -= 10
        
        return reward
    
    def train_episode(self, initial_state: Dict[str, Any], max_steps: int = 100) -> Dict[str, Any]:
        """Train the agent for one episode."""
        state = initial_state.copy()
        total_reward = 0.0
        steps = 0
        
        for step in range(max_steps):
            # Choose action
            action_index, action = self.get_action(state, training=True)
            
            # Simulate action and get next state
            next_state = self.simulate_action(state, action)
            
            # Calculate reward
            reward = self.calculate_reward(state, action, next_state)
            total_reward += reward
            
            # Update Q-value
            done = step == max_steps - 1
            self.update_q_value(state, action_index, reward, next_state, done)
            
            # Move to next state
            state = next_state
            steps += 1
            
            # Early termination if optimal state reached
            if self.is_optimal_state(state):
                break
        
        self.total_episodes += 1
        self.total_reward += total_reward
        self.best_reward = max(self.best_reward, total_reward)
        
        episode_stats = {
            'episode': self.total_episodes,
            'total_reward': total_reward,
            'steps': steps,
            'average_reward': self.total_reward / self.total_episodes,
            'best_reward': self.best_reward
        }
        
        self.episode_rewards.append(total_reward)
        self.episode_steps.append(steps)
        
        return episode_stats
    
    def simulate_action(self, state: Dict[str, Any], action: ActionType) -> Dict[str, Any]:
        """Simulate the effect of an action on the warehouse state."""
        next_state = state.copy()
        
        if action == ActionType.REASSIGN_TASK:
            # Simulate task reassignment: improve load balance
            next_state['load_balance_variance'] = max(0, state.get('load_balance_variance', 0.5) - 0.1)
            next_state['average_efficiency'] = min(1.0, state.get('average_efficiency', 0.5) + 0.05)
        
        elif action == ActionType.ASSIGN_WORKER:
            # Simulate worker assignment: reduce load and improve efficiency
            next_state['load_balance_variance'] = max(0, state.get('load_balance_variance', 0.5) - 0.15)
            next_state['average_efficiency'] = min(1.0, state.get('average_efficiency', 0.5) + 0.1)
            next_state['average_idle_time'] = max(0, state.get('average_idle_time', 0.3) - 0.05)
        
        elif action == ActionType.REDUCE_LOAD:
            # Simulate load reduction
            next_state['load_balance_variance'] = max(0, state.get('load_balance_variance', 0.5) - 0.08)
            next_state['average_idle_time'] = min(1.0, state.get('average_idle_time', 0.3) + 0.03)
        
        elif action == ActionType.INCREASE_CAPACITY:
            # Simulate capacity increase
            next_state['load_balance_variance'] = max(0, state.get('load_balance_variance', 0.5) - 0.12)
            next_state['average_efficiency'] = min(1.0, state.get('average_efficiency', 0.5) + 0.08)
        
        # Add some randomness to simulate real-world uncertainty
        for key in ['load_balance_variance', 'average_efficiency', 'average_idle_time']:
            if key in next_state:
                noise = np.random.normal(0, 0.02)
                next_state[key] = max(0, min(1, next_state[key] + noise))
        
        return next_state
    
    def is_optimal_state(self, state: Dict[str, Any]) -> bool:
        """Check if the current state is optimal."""
        return (state.get('load_balance_variance', 0.5) < 0.1 and 
                state.get('average_efficiency', 0.5) > 0.8 and
                state.get('average_idle_time', 0.3) < 0.2)
    
    def train(self, episodes: int = 1000, initial_states: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Train the Q-learning agent."""
        logger.info(f"Starting Q-learning training with {episodes} episodes")
        
        if initial_states is None:
            # Generate random initial states
            initial_states = [self.generate_random_state() for _ in range(episodes)]
        
        training_start = datetime.utcnow()
        
        for episode in range(episodes):
            initial_state = initial_states[episode % len(initial_states)]
            episode_stats = self.train_episode(initial_state)
            
            if episode % 100 == 0:
                logger.info(f"Episode {episode}: Reward = {episode_stats['total_reward']:.2f}, "
                           f"Avg Reward = {episode_stats['average_reward']:.2f}")
        
        training_end = datetime.utcnow()
        training_duration = (training_end - training_start).total_seconds() * 1000
        
        self.is_trained = True
        self.last_trained = training_end
        
        training_summary = {
            'episodes': episodes,
            'training_duration_ms': training_duration,
            'final_average_reward': self.total_reward / self.total_episodes,
            'best_reward': self.best_reward,
            'convergence_episode': self.find_convergence_episode(),
            'q_table_stats': {
                'max_q_value': np.max(self.q_table),
                'min_q_value': np.min(self.q_table),
                'mean_q_value': np.mean(self.q_table)
            }
        }
        
        self.training_history.append(training_summary)
        logger.info(f"Q-learning training completed. Final avg reward: {training_summary['final_average_reward']:.2f}")
        
        return training_summary
    
    def generate_random_state(self) -> Dict[str, Any]:
        """Generate a random warehouse state for training."""
        return {
            'load_balance_variance': np.random.uniform(0, 0.5),
            'average_efficiency': np.random.uniform(0.3, 0.9),
            'average_idle_time': np.random.uniform(0.1, 0.4),
            'total_workers': np.random.randint(5, 20),
            'total_pending_tasks': np.random.randint(10, 100)
        }
    
    def find_convergence_episode(self) -> int:
        """Find the episode where the agent converged (reward stabilized)."""
        if len(self.episode_rewards) < 100:
            return len(self.episode_rewards)
        
        # Look for stabilization in the last 100 episodes
        recent_rewards = self.episode_rewards[-100:]
        reward_std = np.std(recent_rewards)
        
        # Consider converged if standard deviation is low
        if reward_std < 5.0:
            return max(0, len(self.episode_rewards) - 100)
        
        return len(self.episode_rewards)
    
    def get_optimal_action(self, state: Dict[str, Any]) -> Tuple[ActionType, float]:
        """Get the optimal action for a given state (exploitation only)."""
        if not self.is_trained:
            raise ValueError("Agent must be trained before getting optimal actions")
        
        state_index = self.state_to_index(state)
        action_index = np.argmax(self.q_table[state_index])
        action = list(ActionType)[action_index]
        q_value = self.q_table[state_index, action_index]
        
        return action, float(q_value)
    
    def save_model(self, filepath: str):
        """Save the trained Q-learning model."""
        model_data = {
            'q_table': self.q_table,
            'state_size': self.state_size,
            'action_size': self.action_size,
            'learning_rate': self.learning_rate,
            'discount_factor': self.discount_factor,
            'epsilon': self.epsilon,
            'training_history': self.training_history,
            'episode_rewards': self.episode_rewards,
            'episode_steps': self.episode_steps,
            'total_episodes': self.total_episodes,
            'total_reward': self.total_reward,
            'best_reward': self.best_reward,
            'is_trained': self.is_trained,
            'last_trained': self.last_trained
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"Q-learning model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load a trained Q-learning model."""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.q_table = model_data['q_table']
        self.state_size = model_data['state_size']
        self.action_size = model_data['action_size']
        self.learning_rate = model_data['learning_rate']
        self.discount_factor = model_data['discount_factor']
        self.epsilon = model_data['epsilon']
        self.training_history = model_data['training_history']
        self.episode_rewards = model_data['episode_rewards']
        self.episode_steps = model_data['episode_steps']
        self.total_episodes = model_data['total_episodes']
        self.total_reward = model_data['total_reward']
        self.best_reward = model_data['best_reward']
        self.is_trained = model_data['is_trained']
        self.last_trained = model_data['last_trained']
        
        logger.info(f"Q-learning model loaded from {filepath}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information and performance metrics."""
        return {
            'architecture': {
                'state_size': self.state_size,
                'action_size': self.action_size,
                'learning_rate': self.learning_rate,
                'discount_factor': self.discount_factor,
                'epsilon': self.epsilon
            },
            'training_status': {
                'is_trained': self.is_trained,
                'last_trained': self.last_trained.isoformat() if self.last_trained else None,
                'total_episodes': self.total_episodes,
                'training_sessions': len(self.training_history)
            },
            'performance': {
                'total_reward': self.total_reward,
                'best_reward': self.best_reward,
                'average_reward': self.total_reward / max(1, self.total_episodes),
                'convergence_episode': self.find_convergence_episode() if self.training_history else None
            },
            'q_table_stats': {
                'max_q_value': float(np.max(self.q_table)),
                'min_q_value': float(np.min(self.q_table)),
                'mean_q_value': float(np.mean(self.q_table))
            }
        }


class AdaptiveOptimizer:
    """Wrapper class for adaptive optimization using reinforcement learning."""
    
    def __init__(self, model_path: Optional[str] = None):
        self.agent = QLearningAgent()
        self.model_path = model_path or "./models/adaptive_optimizer.pkl"
        
        if os.path.exists(self.model_path):
            try:
                self.agent.load_model(self.model_path)
                logger.info("Loaded existing adaptive optimizer model")
            except Exception as e:
                logger.warning(f"Failed to load existing model: {e}")
    
    def train_optimizer(self, training_episodes: int = 1000) -> Dict[str, Any]:
        """Train the adaptive optimizer."""
        logger.info(f"Training adaptive optimizer with {training_episodes} episodes")
        
        training_summary = self.agent.train(episodes=training_episodes)
        
        # Save the trained model
        self.agent.save_model(self.model_path)
        
        return training_summary
    
    def get_optimization_recommendation(self, current_state: Dict[str, Any]) -> Dict[str, Any]:
        """Get optimization recommendation based on current warehouse state."""
        if not self.agent.is_trained:
            raise ValueError("Optimizer must be trained before making recommendations")
        
        action, q_value = self.agent.get_optimal_action(current_state)
        
        # Generate recommendation details based on action
        recommendation = self.action_to_recommendation(action, current_state, q_value)
        
        return recommendation
    
    def action_to_recommendation(self, action: ActionType, state: Dict[str, Any], q_value: float) -> Dict[str, Any]:
        """Convert Q-learning action to human-readable recommendation."""
        base_recommendation = {
            'action_type': action.value,
            'confidence': min(0.95, max(0.1, abs(q_value) / 10.0)),
            'q_value': float(q_value),
            'reasoning': self.get_action_reasoning(action, state)
        }
        
        if action == ActionType.REASSIGN_TASK:
            base_recommendation.update({
                'title': 'Preporučuje se preraspodjela zadataka',
                'description': 'Balansiranje opterećenja između radnji će poboljšati efikasnost',
                'estimated_impact': {
                    'load_balance_improvement': 15.0,
                    'efficiency_improvement': 8.0
                }
            })
        elif action == ActionType.ASSIGN_WORKER:
            base_recommendation.update({
                'title': 'Preporučuje se dodavanje radnika',
                'description': 'Dodatni radnik će smanjiti opterećenje i poboljšati performanse',
                'estimated_impact': {
                    'load_balance_improvement': 25.0,
                    'efficiency_improvement': 15.0
                }
            })
        elif action == ActionType.REDUCE_LOAD:
            base_recommendation.update({
                'title': 'Preporučuje se smanjenje opterećenja',
                'description': 'Smanjenje trenutnog opterećenja će poboljšati kvalitet rada',
                'estimated_impact': {
                    'load_balance_improvement': 20.0,
                    'quality_improvement': 10.0
                }
            })
        elif action == ActionType.INCREASE_CAPACITY:
            base_recommendation.update({
                'title': 'Preporučuje se povećanje kapaciteta',
                'description': 'Povećanje kapaciteta će omogućiti bolje iskorišćenje resursa',
                'estimated_impact': {
                    'capacity_improvement': 30.0,
                    'efficiency_improvement': 12.0
                }
            })
        else:
            base_recommendation.update({
                'title': 'Trenutno stanje je optimalno',
                'description': 'Nema potrebe za promenama u trenutnom stanju',
                'estimated_impact': {
                    'stability_improvement': 5.0
                }
            })
        
        return base_recommendation
    
    def get_action_reasoning(self, action: ActionType, state: Dict[str, Any]) -> str:
        """Generate human-readable reasoning for the recommended action."""
        load_variance = state.get('load_balance_variance', 0.5)
        efficiency = state.get('average_efficiency', 0.5)
        idle_time = state.get('average_idle_time', 0.3)
        
        if action == ActionType.REASSIGN_TASK:
            return f"Visoka varijansa opterećenja ({load_variance:.1%}) ukazuje na potrebu za balansiranjem zadataka"
        elif action == ActionType.ASSIGN_WORKER:
            return f"Niska efikasnost ({efficiency:.1%}) i visoko opterećenje zahtevaju dodatne resurse"
        elif action == ActionType.REDUCE_LOAD:
            return f"Preopterećenje sistema ({load_variance:.1%}) može uticati na kvalitet rada"
        elif action == ActionType.INCREASE_CAPACITY:
            return f"Visoko neaktivno vreme ({idle_time:.1%}) ukazuje na neiskorišćen kapacitet"
        else:
            return f"Sistem je u optimalnom stanju (efikasnost: {efficiency:.1%}, opterećenje: {load_variance:.1%})"
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model status and performance metrics."""
        return self.agent.get_model_info()
