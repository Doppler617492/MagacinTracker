from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app_common.logging import get_logger
from app_common.security import require_role, UserRole

from ..models.neural_network import WorkerPerformancePredictor
from ..models.reinforcement_learning import AdaptiveOptimizer

logger = get_logger(__name__)
router = APIRouter()


class OptimizationRequest(BaseModel):
    current_state: Dict[str, Any]
    optimization_type: str = "adaptive"  # "adaptive" or "predictive"


class OptimizationResponse(BaseModel):
    recommendation_id: str
    optimization_type: str
    recommended_action: Dict[str, Any]
    confidence: float
    expected_improvement: Dict[str, float]
    reasoning: str
    processing_time_ms: float
    generated_at: datetime


@router.post("/optimize", response_model=OptimizationResponse)
async def get_optimization_recommendation(
    request: Request,
    optimization_request: OptimizationRequest,
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> OptimizationResponse:
    """
    Get AI optimization recommendations based on current warehouse state.
    
    This endpoint analyzes the current state and returns intelligent
    recommendations for load balancing, resource allocation, and efficiency optimization.
    """
    start_time = datetime.utcnow()
    recommendation_id = f"opt_{int(start_time.timestamp())}"
    
    try:
        current_state = optimization_request.current_state
        
        if optimization_request.optimization_type == "adaptive":
            # Use reinforcement learning for adaptive optimization
            optimizer = AdaptiveOptimizer()
            
            if not optimizer.agent.is_trained:
                # If not trained, provide basic recommendations
                recommendation = generate_basic_recommendation(current_state)
                confidence = 0.6
            else:
                # Get AI recommendation
                recommendation = optimizer.get_optimization_recommendation(current_state)
                confidence = recommendation.get('confidence', 0.8)
            
        elif optimization_request.optimization_type == "predictive":
            # Use neural network for predictive optimization
            predictor = WorkerPerformancePredictor()
            
            if not predictor.model.is_trained:
                recommendation = generate_basic_recommendation(current_state)
                confidence = 0.6
            else:
                # Generate predictive recommendations
                recommendation = generate_predictive_recommendation(current_state, predictor)
                confidence = 0.85
            
        else:
            raise HTTPException(status_code=400, detail="Nepoznat tip optimizacije")
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "AI_OPTIMIZATION_GENERATED",
            recommendation_id=recommendation_id,
            optimization_type=optimization_request.optimization_type,
            confidence=confidence,
            processing_time_ms=processing_time,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        
        return OptimizationResponse(
            recommendation_id=recommendation_id,
            optimization_type=optimization_request.optimization_type,
            recommended_action=recommendation,
            confidence=confidence,
            expected_improvement=recommendation.get('estimated_impact', {}),
            reasoning=recommendation.get('reasoning', ''),
            processing_time_ms=processing_time,
            generated_at=datetime.utcnow()
        )
        
    except Exception as e:
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.error(
            "AI_OPTIMIZATION_ERROR",
            recommendation_id=recommendation_id,
            optimization_type=optimization_request.optimization_type,
            error=str(e),
            processing_time_ms=processing_time,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        raise HTTPException(status_code=500, detail=f"Greška pri generisanju optimizacije: {str(e)}")


def generate_basic_recommendation(current_state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate basic recommendation when AI models are not trained."""
    load_variance = current_state.get('load_balance_variance', 0.5)
    efficiency = current_state.get('average_efficiency', 0.5)
    idle_time = current_state.get('average_idle_time', 0.3)
    
    if load_variance > 0.3:
        return {
            'action_type': 'load_balance',
            'title': 'Preporučuje se balansiranje opterećenja',
            'description': f'Visoka varijansa opterećenja ({load_variance:.1%}) ukazuje na potrebu za preraspodelom zadataka',
            'estimated_impact': {
                'load_balance_improvement': 20.0,
                'efficiency_improvement': 10.0
            },
            'reasoning': 'Osnovna analiza pokazuje neravnomerno opterećenje'
        }
    elif efficiency < 0.6:
        return {
            'action_type': 'efficiency_optimization',
            'title': 'Preporučuje se poboljšanje efikasnosti',
            'description': f'Niska efikasnost ({efficiency:.1%}) zahteva intervenciju',
            'estimated_impact': {
                'efficiency_improvement': 15.0,
                'quality_improvement': 8.0
            },
            'reasoning': 'Osnovna analiza pokazuje nisku efikasnost rada'
        }
    elif idle_time > 0.4:
        return {
            'action_type': 'resource_optimization',
            'title': 'Preporučuje se optimizacija resursa',
            'description': f'Visoko neaktivno vreme ({idle_time:.1%}) ukazuje na neiskorišćen kapacitet',
            'estimated_impact': {
                'resource_utilization_improvement': 25.0,
                'efficiency_improvement': 12.0
            },
            'reasoning': 'Osnovna analiza pokazuje neiskorišćen kapacitet'
        }
    else:
        return {
            'action_type': 'no_action',
            'title': 'Trenutno stanje je optimalno',
            'description': 'Nema potrebe za promenama u trenutnom stanju',
            'estimated_impact': {
                'stability_improvement': 5.0
            },
            'reasoning': 'Osnovna analiza pokazuje da je sistem u dobrom stanju'
        }


def generate_predictive_recommendation(current_state: Dict[str, Any], predictor: WorkerPerformancePredictor) -> Dict[str, Any]:
    """Generate predictive recommendation using neural network."""
    # Mock worker data for prediction
    worker_data = {
        'current_tasks': current_state.get('total_pending_tasks', 50) // current_state.get('total_workers', 5),
        'completed_tasks_today': 25,
        'avg_completion_time': 4.5,
        'efficiency_score': current_state.get('average_efficiency', 0.5),
        'idle_time_percentage': current_state.get('average_idle_time', 0.3),
        'day_of_week': datetime.now().weekday(),
        'hour_of_day': datetime.now().hour,
        'store_load_index': current_state.get('load_balance_variance', 0.5)
    }
    
    # Get prediction
    prediction_result = predictor.predict_performance(worker_data)
    predicted_performance = prediction_result['predicted_performance']
    
    if predicted_performance < 0.6:
        return {
            'action_type': 'predictive_optimization',
            'title': 'AI predviđa pad performansi',
            'description': f'Neuralna mreža predviđa performanse od {predicted_performance:.1%} - potrebna je intervencija',
            'estimated_impact': {
                'performance_improvement': 20.0,
                'efficiency_improvement': 15.0
            },
            'reasoning': f'Prediktivni model ukazuje na potencijalni pad performansi do {predicted_performance:.1%}'
        }
    else:
        return {
            'action_type': 'maintain_current',
            'title': 'AI predviđa stabilne performanse',
            'description': f'Neuralna mreža predviđa dobre performanse ({predicted_performance:.1%})',
            'estimated_impact': {
                'stability_improvement': 10.0
            },
            'reasoning': f'Prediktivni model ukazuje na stabilne performanse od {predicted_performance:.1%}'
        }
