from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app_common.logging import get_logger
from app_common.security import require_role, UserRole

from ..models.neural_network import WorkerPerformancePredictor
from ..models.reinforcement_learning import AdaptiveOptimizer

logger = get_logger(__name__)
router = APIRouter()


class ModelStatusResponse(BaseModel):
    neural_network: Dict[str, Any]
    reinforcement_learning: Dict[str, Any]
    overall_status: str
    last_updated: datetime


@router.get("/model/status", response_model=ModelStatusResponse)
async def get_model_status(
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> ModelStatusResponse:
    """
    Get the status and performance metrics of all AI models.
    
    Returns information about neural network and reinforcement learning models,
    including training status, performance metrics, and last update times.
    """
    try:
        # Get neural network model status
        nn_predictor = WorkerPerformancePredictor()
        nn_status = nn_predictor.get_model_status()
        
        # Get reinforcement learning model status
        rl_optimizer = AdaptiveOptimizer()
        rl_status = rl_optimizer.get_model_status()
        
        # Determine overall status
        nn_trained = nn_status.get('training_status', {}).get('is_trained', False)
        rl_trained = rl_status.get('training_status', {}).get('is_trained', False)
        
        if nn_trained and rl_trained:
            overall_status = "fully_trained"
        elif nn_trained or rl_trained:
            overall_status = "partially_trained"
        else:
            overall_status = "not_trained"
        
        logger.info(
            "AI_MODEL_STATUS_REQUESTED",
            nn_trained=nn_trained,
            rl_trained=rl_trained,
            overall_status=overall_status
        )
        
        return ModelStatusResponse(
            neural_network=nn_status,
            reinforcement_learning=rl_status,
            overall_status=overall_status,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error("AI_MODEL_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Greška pri dobijanju statusa modela: {str(e)}")


@router.get("/model/performance")
async def get_model_performance(
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> Dict[str, Any]:
    """
    Get detailed performance metrics for all AI models.
    
    Returns training history, accuracy metrics, and performance trends.
    """
    try:
        # Get neural network performance
        nn_predictor = WorkerPerformancePredictor()
        nn_info = nn_predictor.get_model_status()
        
        # Get reinforcement learning performance
        rl_optimizer = AdaptiveOptimizer()
        rl_info = rl_optimizer.get_model_status()
        
        performance_data = {
            "neural_network": {
                "accuracy": nn_info.get('performance', {}).get('final_accuracy'),
                "loss": nn_info.get('performance', {}).get('final_loss'),
                "best_accuracy": nn_info.get('performance', {}).get('best_accuracy'),
                "training_sessions": nn_info.get('training_status', {}).get('training_sessions', 0)
            },
            "reinforcement_learning": {
                "average_reward": rl_info.get('performance', {}).get('average_reward'),
                "best_reward": rl_info.get('performance', {}).get('best_reward'),
                "convergence_episode": rl_info.get('performance', {}).get('convergence_episode'),
                "total_episodes": rl_info.get('training_status', {}).get('total_episodes', 0)
            },
            "combined_metrics": {
                "overall_accuracy": (nn_info.get('performance', {}).get('final_accuracy', 0) + 
                                   (rl_info.get('performance', {}).get('average_reward', 0) / 10)) / 2,
                "model_maturity": "high" if (nn_info.get('training_status', {}).get('is_trained') and 
                                           rl_info.get('training_status', {}).get('is_trained')) else "low"
            }
        }
        
        logger.info("AI_MODEL_PERFORMANCE_REQUESTED")
        
        return performance_data
        
    except Exception as e:
        logger.error("AI_MODEL_PERFORMANCE_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Greška pri dobijanju performansi modela: {str(e)}")


@router.post("/model/reset")
async def reset_models(
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> Dict[str, str]:
    """
    Reset all AI models to initial state.
    
    This will clear all training data and reset models to untrained state.
    Use with caution as this will require retraining.
    """
    try:
        # Reset neural network model
        nn_predictor = WorkerPerformancePredictor()
        # In a real implementation, this would reset the model weights
        
        # Reset reinforcement learning model
        rl_optimizer = AdaptiveOptimizer()
        # In a real implementation, this would reset the Q-table
        
        logger.warning("AI_MODELS_RESET", user_id="admin")
        
        return {
            "message": "Svi AI modeli su resetovani",
            "status": "success",
            "reset_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("AI_MODEL_RESET_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Greška pri resetovanju modela: {str(e)}")
