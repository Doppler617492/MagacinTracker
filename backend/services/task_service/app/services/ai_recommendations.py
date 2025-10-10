import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import statistics
from dataclasses import dataclass
from enum import Enum

from app_common.logging import get_logger

logger = get_logger(__name__)


class RecommendationType(str, Enum):
    LOAD_BALANCE = "load_balance"
    RESOURCE_ALLOCATION = "resource_allocation"
    TASK_REASSIGNMENT = "task_reassignment"
    EFFICIENCY_OPTIMIZATION = "efficiency_optimization"


class RecommendationPriority(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class WorkerMetrics:
    worker_id: str
    worker_name: str
    current_tasks: int
    completed_tasks_today: int
    avg_completion_time: float
    efficiency_score: float
    idle_time_percentage: float
    location: str


@dataclass
class StoreMetrics:
    store_id: str
    store_name: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    avg_completion_time: float
    worker_count: int
    load_index: float
    efficiency_delta: float


@dataclass
class Recommendation:
    id: str
    type: RecommendationType
    priority: RecommendationPriority
    title: str
    description: str
    confidence: float
    impact_score: float
    actions: List[Dict[str, Any]]
    estimated_improvement: Dict[str, float]
    reasoning: str
    created_at: datetime


class AIRecommendationEngine:
    """AI engine for generating operational recommendations."""
    
    def __init__(self):
        self.load_threshold_high = 0.85  # 85% load considered high
        self.load_threshold_low = 0.30   # 30% load considered low
        self.efficiency_threshold = 0.70  # 70% efficiency threshold
        self.idle_threshold = 0.20       # 20% idle time threshold
    
    def generate_recommendations(
        self,
        worker_metrics: List[WorkerMetrics],
        store_metrics: List[StoreMetrics],
        historical_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """
        Generate AI recommendations based on current metrics and historical data.
        """
        recommendations = []
        
        # Load balancing recommendations
        load_recs = self._generate_load_balance_recommendations(worker_metrics, store_metrics)
        recommendations.extend(load_recs)
        
        # Resource allocation recommendations
        resource_recs = self._generate_resource_allocation_recommendations(worker_metrics, store_metrics)
        recommendations.extend(resource_recs)
        
        # Task reassignment recommendations
        task_recs = self._generate_task_reassignment_recommendations(worker_metrics, store_metrics)
        recommendations.extend(task_recs)
        
        # Efficiency optimization recommendations
        efficiency_recs = self._generate_efficiency_recommendations(worker_metrics, store_metrics, historical_data)
        recommendations.extend(efficiency_recs)
        
        # Sort by priority and confidence
        recommendations.sort(key=lambda r: (r.priority.value, -r.confidence), reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _generate_load_balance_recommendations(
        self,
        worker_metrics: List[WorkerMetrics],
        store_metrics: List[StoreMetrics]
    ) -> List[Recommendation]:
        """Generate load balancing recommendations."""
        recommendations = []
        
        # Find overloaded and underloaded stores
        overloaded_stores = [s for s in store_metrics if s.load_index > self.load_threshold_high]
        underloaded_stores = [s for s in store_metrics if s.load_index < self.load_threshold_low]
        
        for overloaded in overloaded_stores:
            for underloaded in underloaded_stores:
                if overloaded.store_id != underloaded.store_id:
                    # Calculate optimal task redistribution
                    tasks_to_move = self._calculate_optimal_redistribution(overloaded, underloaded)
                    
                    if tasks_to_move > 0:
                        confidence = min(0.95, 0.7 + (overloaded.load_index - underloaded.load_index) * 0.5)
                        impact = (overloaded.load_index - underloaded.load_index) * 100
                        
                        recommendation = Recommendation(
                            id=f"load_balance_{overloaded.store_id}_{underloaded.store_id}",
                            type=RecommendationType.LOAD_BALANCE,
                            priority=RecommendationPriority.HIGH if impact > 30 else RecommendationPriority.MEDIUM,
                            title=f"Premjesti {tasks_to_move} zadataka iz {overloaded.store_name} u {underloaded.store_name}",
                            description=f"Radnja {overloaded.store_name} je preopterećena ({overloaded.load_index:.1%}), dok {underloaded.store_name} ima kapacitet ({underloaded.load_index:.1%})",
                            confidence=confidence,
                            impact_score=impact,
                            actions=[
                                {
                                    "type": "reassign_tasks",
                                    "from_store": overloaded.store_id,
                                    "to_store": underloaded.store_id,
                                    "task_count": tasks_to_move
                                }
                            ],
                            estimated_improvement={
                                "load_balance": 15.0,
                                "efficiency": 8.0,
                                "completion_time": -12.0
                            },
                            reasoning=f"Balansiranje opterećenja između radnji će smanjiti čekanje u {overloaded.store_name} i povećati iskorišćenost {underloaded.store_name}",
                            created_at=datetime.utcnow()
                        )
                        recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_resource_allocation_recommendations(
        self,
        worker_metrics: List[WorkerMetrics],
        store_metrics: List[StoreMetrics]
    ) -> List[Recommendation]:
        """Generate resource allocation recommendations."""
        recommendations = []
        
        # Find stores that need additional workers
        for store in store_metrics:
            if store.load_index > self.load_threshold_high and store.worker_count < 5:  # Max 5 workers per store
                # Find available workers from other stores
                available_workers = [w for w in worker_metrics 
                                   if w.location != store.store_id and w.idle_time_percentage > self.idle_threshold]
                
                if available_workers:
                    best_worker = max(available_workers, key=lambda w: w.efficiency_score)
                    confidence = 0.8 + (store.load_index - 0.85) * 0.5
                    impact = (store.load_index - 0.85) * 100
                    
                    recommendation = Recommendation(
                        id=f"resource_allocation_{store.store_id}_{best_worker.worker_id}",
                        type=RecommendationType.RESOURCE_ALLOCATION,
                        priority=RecommendationPriority.HIGH if impact > 20 else RecommendationPriority.MEDIUM,
                        title=f"Dodaj {best_worker.worker_name} u {store.store_name}",
                        description=f"Radnja {store.store_name} je preopterećena ({store.load_index:.1%}) i treba dodatnu pomoć",
                        confidence=confidence,
                        impact_score=impact,
                        actions=[
                            {
                                "type": "assign_worker",
                                "worker_id": best_worker.worker_id,
                                "to_store": store.store_id,
                                "duration_hours": 4
                            }
                        ],
                        estimated_improvement={
                            "load_balance": 20.0,
                            "efficiency": 12.0,
                            "completion_time": -18.0
                        },
                        reasoning=f"Dodavanje efikasnog radnika {best_worker.worker_name} (efikasnost: {best_worker.efficiency_score:.1%}) će značajno smanjiti opterećenje",
                        created_at=datetime.utcnow()
                    )
                    recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_task_reassignment_recommendations(
        self,
        worker_metrics: List[WorkerMetrics],
        store_metrics: List[StoreMetrics]
    ) -> List[Recommendation]:
        """Generate task reassignment recommendations."""
        recommendations = []
        
        # Find overloaded and underloaded workers
        overloaded_workers = [w for w in worker_metrics if w.current_tasks > 8]  # More than 8 tasks
        underloaded_workers = [w for w in worker_metrics if w.current_tasks < 3 and w.idle_time_percentage > 0.3]
        
        for overloaded in overloaded_workers:
            for underloaded in underloaded_workers:
                if overloaded.location == underloaded.location:  # Same store
                    tasks_to_reassign = min(2, overloaded.current_tasks - 5)  # Reassign 2 tasks max
                    
                    if tasks_to_reassign > 0:
                        confidence = 0.75 + (overloaded.current_tasks - underloaded.current_tasks) * 0.05
                        impact = (overloaded.current_tasks - underloaded.current_tasks) * 5
                        
                        recommendation = Recommendation(
                            id=f"task_reassign_{overloaded.worker_id}_{underloaded.worker_id}",
                            type=RecommendationType.TASK_REASSIGNMENT,
                            priority=RecommendationPriority.MEDIUM,
                            title=f"Premjesti {tasks_to_reassign} zadataka sa {overloaded.worker_name} na {underloaded.worker_name}",
                            description=f"{overloaded.worker_name} ima {overloaded.current_tasks} zadataka, {underloaded.worker_name} ima {underloaded.current_tasks}",
                            confidence=confidence,
                            impact_score=impact,
                            actions=[
                                {
                                    "type": "reassign_worker_tasks",
                                    "from_worker": overloaded.worker_id,
                                    "to_worker": underloaded.worker_id,
                                    "task_count": tasks_to_reassign
                                }
                            ],
                            estimated_improvement={
                                "efficiency": 10.0,
                                "completion_time": -8.0,
                                "worker_satisfaction": 15.0
                            },
                            reasoning=f"Ravnomjerna raspodjela zadataka će poboljšati efikasnost i smanjiti stres kod preopterećenih radnika",
                            created_at=datetime.utcnow()
                        )
                        recommendations.append(recommendation)
        
        return recommendations
    
    def _generate_efficiency_recommendations(
        self,
        worker_metrics: List[WorkerMetrics],
        store_metrics: List[StoreMetrics],
        historical_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Generate efficiency optimization recommendations."""
        recommendations = []
        
        # Find low-efficiency workers
        low_efficiency_workers = [w for w in worker_metrics if w.efficiency_score < self.efficiency_threshold]
        
        for worker in low_efficiency_workers:
            # Analyze historical performance
            historical_performance = historical_data.get(worker.worker_id, {})
            avg_historical_efficiency = historical_performance.get("avg_efficiency", 0.7)
            
            if worker.efficiency_score < avg_historical_efficiency * 0.8:  # 20% below historical
                confidence = 0.85
                impact = (avg_historical_efficiency - worker.efficiency_score) * 100
                
                recommendation = Recommendation(
                    id=f"efficiency_optimization_{worker.worker_id}",
                    type=RecommendationType.EFFICIENCY_OPTIMIZATION,
                    priority=RecommendationPriority.MEDIUM,
                    title=f"Optimizuj performanse {worker.worker_name}",
                    description=f"Efikasnost {worker.worker_name} je {worker.efficiency_score:.1%}, ispod proseka od {avg_historical_efficiency:.1%}",
                    confidence=confidence,
                    impact_score=impact,
                    actions=[
                        {
                            "type": "provide_training",
                            "worker_id": worker.worker_id,
                            "training_type": "efficiency_improvement",
                            "duration_hours": 2
                        },
                        {
                            "type": "reduce_task_complexity",
                            "worker_id": worker.worker_id,
                            "complexity_reduction": 0.2
                        }
                    ],
                    estimated_improvement={
                        "efficiency": 15.0,
                        "completion_time": -10.0,
                        "quality": 8.0
                    },
                    reasoning=f"Trenutna efikasnost je značajno ispod istorijskog proseka, potrebna je intervencija",
                    created_at=datetime.utcnow()
                )
                recommendations.append(recommendation)
        
        return recommendations
    
    def _calculate_optimal_redistribution(self, overloaded_store: StoreMetrics, underloaded_store: StoreMetrics) -> int:
        """Calculate optimal number of tasks to redistribute."""
        # Simple heuristic: move tasks until both stores are at 70% load
        target_load = 0.70
        
        overloaded_capacity = overloaded_store.worker_count * 10  # 10 tasks per worker capacity
        underloaded_capacity = underloaded_store.worker_count * 10
        
        overloaded_target_tasks = int(overloaded_capacity * target_load)
        underloaded_target_tasks = int(underloaded_capacity * target_load)
        
        current_overloaded = overloaded_store.pending_tasks
        current_underloaded = underloaded_store.pending_tasks
        
        tasks_to_move = min(
            current_overloaded - overloaded_target_tasks,
            underloaded_target_tasks - current_underloaded
        )
        
        return max(0, tasks_to_move)
    
    def simulate_load_balance_scenario(
        self,
        worker_metrics: List[WorkerMetrics],
        store_metrics: List[StoreMetrics],
        recommendation: Recommendation
    ) -> Dict[str, Any]:
        """Simulate what-if scenario for a recommendation."""
        # Create copies for simulation
        sim_worker_metrics = [WorkerMetrics(**w.__dict__) for w in worker_metrics]
        sim_store_metrics = [StoreMetrics(**s.__dict__) for s in store_metrics]
        
        # Apply recommendation actions
        for action in recommendation.actions:
            if action["type"] == "reassign_tasks":
                from_store = next(s for s in sim_store_metrics if s.store_id == action["from_store"])
                to_store = next(s for s in sim_store_metrics if s.store_id == action["to_store"])
                
                tasks_to_move = action["task_count"]
                from_store.pending_tasks -= tasks_to_move
                to_store.pending_tasks += tasks_to_move
                
                # Recalculate load indices
                from_store.load_index = from_store.pending_tasks / (from_store.worker_count * 10)
                to_store.load_index = to_store.pending_tasks / (to_store.worker_count * 10)
            
            elif action["type"] == "assign_worker":
                # Simulate worker assignment
                target_store = next(s for s in sim_store_metrics if s.store_id == action["to_store"])
                target_store.worker_count += 1
                target_store.load_index = target_store.pending_tasks / (target_store.worker_count * 10)
        
        # Calculate simulation results
        total_load_variance = statistics.stdev([s.load_index for s in sim_store_metrics])
        avg_efficiency = statistics.mean([w.efficiency_score for w in sim_worker_metrics])
        total_idle_time = statistics.mean([w.idle_time_percentage for w in sim_worker_metrics])
        
        return {
            "after_simulation": {
                "store_metrics": [
                    {
                        "store_id": s.store_id,
                        "store_name": s.store_name,
                        "load_index": s.load_index,
                        "worker_count": s.worker_count,
                        "pending_tasks": s.pending_tasks
                    }
                    for s in sim_store_metrics
                ],
                "overall_metrics": {
                    "load_balance_variance": total_load_variance,
                    "average_efficiency": avg_efficiency,
                    "average_idle_time": total_idle_time,
                    "total_workers": sum(s.worker_count for s in sim_store_metrics),
                    "total_pending_tasks": sum(s.pending_tasks for s in sim_store_metrics)
                }
            },
            "improvement_metrics": {
                "load_balance_improvement": recommendation.estimated_improvement.get("load_balance", 0),
                "efficiency_improvement": recommendation.estimated_improvement.get("efficiency", 0),
                "completion_time_improvement": recommendation.estimated_improvement.get("completion_time", 0)
            }
        }


# Global AI recommendation engine instance
ai_recommendation_engine = AIRecommendationEngine()


def generate_ai_recommendations(
    worker_metrics: List[WorkerMetrics],
    store_metrics: List[StoreMetrics],
    historical_data: Dict[str, Any]
) -> List[Recommendation]:
    """Generate AI recommendations using the global engine."""
    return ai_recommendation_engine.generate_recommendations(worker_metrics, store_metrics, historical_data)


def simulate_recommendation_scenario(
    worker_metrics: List[WorkerMetrics],
    store_metrics: List[StoreMetrics],
    recommendation: Recommendation
) -> Dict[str, Any]:
    """Simulate recommendation scenario using the global engine."""
    return ai_recommendation_engine.simulate_load_balance_scenario(worker_metrics, store_metrics, recommendation)
