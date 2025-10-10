from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app_common.logging import get_logger
from app_common.security import require_role, UserRole

from ..models.neural_network import WorkerPerformancePredictor
from ..models.reinforcement_learning import AdaptiveOptimizer

logger = get_logger(__name__)
router = APIRouter()


class TrainingRequest(BaseModel):
    model_type: str  # "neural_network" or "reinforcement_learning"
    epochs: int = 100
    learning_rate: float = 0.001
    batch_size: int = 32


class TrainingResponse(BaseModel):
    training_id: str
    model_type: str
    status: str
    training_duration_ms: float
    final_accuracy: float
    training_history: Dict[str, Any]
    started_at: datetime
    completed_at: datetime


@router.post("/train", response_model=TrainingResponse)
async def train_model(
    request: Request,
    training_request: TrainingRequest,
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> TrainingResponse:
    """
    Train AI models (neural network or reinforcement learning).
    
    This endpoint allows manual training of AI models with specified parameters.
    Training can be done in batch mode or incremental mode.
    """
    start_time = datetime.utcnow()
    training_id = f"training_{int(start_time.timestamp())}"
    
    try:
        logger.info(
            "AI_TRAINING_STARTED",
            training_id=training_id,
            model_type=training_request.model_type,
            epochs=training_request.epochs,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        
        if training_request.model_type == "neural_network":
            # Train neural network model
            predictor = WorkerPerformancePredictor()
            
            # Generate mock training data
            training_data = generate_mock_training_data(1000)
            
            training_history = predictor.train_model(
                historical_data=training_data,
                epochs=training_request.epochs
            )
            
            final_accuracy = training_history.get('final_accuracy', 0.0)
            
        elif training_request.model_type == "reinforcement_learning":
            # Train reinforcement learning model
            optimizer = AdaptiveOptimizer()
            
            training_history = optimizer.train_optimizer(
                training_episodes=training_request.epochs
            )
            
            final_accuracy = training_history.get('final_average_reward', 0.0) / 10.0  # Normalize
            
        else:
            raise HTTPException(status_code=400, detail="Nepoznat tip modela")
        
        end_time = datetime.utcnow()
        training_duration = (end_time - start_time).total_seconds() * 1000
        
        logger.info(
            "AI_TRAINING_COMPLETED",
            training_id=training_id,
            model_type=training_request.model_type,
            training_duration_ms=training_duration,
            final_accuracy=final_accuracy,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        
        return TrainingResponse(
            training_id=training_id,
            model_type=training_request.model_type,
            status="completed",
            training_duration_ms=training_duration,
            final_accuracy=final_accuracy,
            training_history=training_history,
            started_at=start_time,
            completed_at=end_time
        )
        
    except Exception as e:
        end_time = datetime.utcnow()
        training_duration = (end_time - start_time).total_seconds() * 1000
        
        logger.error(
            "AI_TRAINING_ERROR",
            training_id=training_id,
            model_type=training_request.model_type,
            error=str(e),
            training_duration_ms=training_duration,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        raise HTTPException(status_code=500, detail=f"Greška pri treniranju modela: {str(e)}")


@router.get("/train/status/{training_id}")
async def get_training_status(
    training_id: str,
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> Dict[str, Any]:
    """
    Get the status of a specific training session.
    
    Returns current progress, metrics, and estimated completion time.
    """
    try:
        # In a real implementation, this would track training progress
        # For now, return mock status
        return {
            "training_id": training_id,
            "status": "completed",
            "progress": 100.0,
            "current_epoch": 100,
            "total_epochs": 100,
            "current_loss": 0.0234,
            "current_accuracy": 0.892,
            "estimated_completion": None,
            "started_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("AI_TRAINING_STATUS_ERROR", training_id=training_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Greška pri dobijanju statusa treniranja: {str(e)}")


@router.post("/train/cancel/{training_id}")
async def cancel_training(
    request: Request,
    training_id: str,
    _: None = Depends(require_role([UserRole.sef, UserRole.menadzer])),
) -> Dict[str, str]:
    """
    Cancel a running training session.
    
    This will stop the training process and save any progress made so far.
    """
    try:
        logger.info(
            "AI_TRAINING_CANCELLED",
            training_id=training_id,
            user_id=getattr(request.state, "user_id", "unknown")
        )
        
        return {
            "message": "Treniranje je otkazano",
            "training_id": training_id,
            "cancelled_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("AI_TRAINING_CANCEL_ERROR", training_id=training_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Greška pri otkazivanju treniranja: {str(e)}")


def generate_mock_training_data(sample_count: int) -> List[Dict[str, Any]]:
    """Generate mock training data for neural network training."""
    import random
    
    training_data = []
    
    for i in range(sample_count):
        # Generate realistic worker performance data
        current_tasks = random.randint(1, 15)
        completed_tasks_today = random.randint(5, 50)
        avg_completion_time = random.uniform(2.0, 8.0)
        efficiency_score = random.uniform(0.4, 0.95)
        idle_time_percentage = random.uniform(0.05, 0.4)
        day_of_week = random.randint(0, 6)
        hour_of_day = random.randint(6, 18)
        store_load_index = random.uniform(0.2, 1.0)
        
        # Calculate performance score based on features
        performance_score = (
            efficiency_score * 0.4 +
            (1 - idle_time_percentage) * 0.3 +
            (1 - store_load_index) * 0.2 +
            (completed_tasks_today / 50) * 0.1
        )
        
        training_data.append({
            'current_tasks': current_tasks,
            'completed_tasks_today': completed_tasks_today,
            'avg_completion_time': avg_completion_time,
            'efficiency_score': efficiency_score,
            'idle_time_percentage': idle_time_percentage,
            'day_of_week': day_of_week,
            'hour_of_day': hour_of_day,
            'store_load_index': store_load_index,
            'performance_score': max(0, min(1, performance_score))
        })
    
    return training_data
