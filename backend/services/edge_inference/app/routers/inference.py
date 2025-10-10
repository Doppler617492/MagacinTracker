from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app_common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class PredictionRequest(BaseModel):
    model_id: str = "default"
    features: List[float]
    request_id: str = None


class PredictionResponse(BaseModel):
    prediction: float
    confidence: float
    inference_time_ms: float
    model_version: int
    edge_mode: bool
    request_id: str
    timestamp: datetime


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: Request,
    prediction_request: PredictionRequest,
) -> PredictionResponse:
    """
    Make fast prediction using edge model.
    
    This endpoint provides sub-200ms inference for real-time predictions
    even when the backend is offline.
    """
    start_time = datetime.utcnow()
    
    try:
        # Get edge manager from app state
        edge_manager = request.app.state.edge_manager
        
        # Validate features
        if len(prediction_request.features) != 8:
            raise HTTPException(
                status_code=400, 
                detail="Expected 8 features for prediction"
            )
        
        # Make prediction
        result = edge_manager.predict(
            model_id=prediction_request.model_id,
            features=prediction_request.features
        )
        
        # Calculate total request time
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "EDGE_PREDICTION_COMPLETED",
            model_id=prediction_request.model_id,
            inference_time_ms=result['inference_time_ms'],
            total_time_ms=total_time,
            confidence=result['confidence']
        )
        
        return PredictionResponse(
            prediction=result['prediction'],
            confidence=result['confidence'],
            inference_time_ms=result['inference_time_ms'],
            model_version=result['model_version'],
            edge_mode=result['edge_mode'],
            request_id=prediction_request.request_id or f"edge_{int(start_time.timestamp())}",
            timestamp=datetime.utcnow()
        )
        
    except ValueError as e:
        logger.error("EDGE_PREDICTION_ERROR", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        logger.error("EDGE_PREDICTION_ERROR", error=str(e), total_time_ms=total_time)
        raise HTTPException(status_code=500, detail=f"Edge prediction failed: {str(e)}")


@router.get("/models/{model_id}/status")
async def get_model_status(
    request: Request,
    model_id: str,
) -> Dict[str, Any]:
    """
    Get status of a specific edge model.
    
    Returns model performance statistics, version info, and health status.
    """
    try:
        edge_manager = request.app.state.edge_manager
        status = edge_manager.get_model_status(model_id)
        
        logger.info("EDGE_MODEL_STATUS_REQUESTED", model_id=model_id)
        
        return status
        
    except Exception as e:
        logger.error("EDGE_MODEL_STATUS_ERROR", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get model status: {str(e)}")


@router.get("/system/status")
async def get_system_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Get overall edge inference system status.
    
    Returns information about all models, sync status, and performance metrics.
    """
    try:
        edge_manager = request.app.state.edge_manager
        status = edge_manager.get_system_status()
        
        logger.info("EDGE_SYSTEM_STATUS_REQUESTED")
        
        return status
        
    except Exception as e:
        logger.error("EDGE_SYSTEM_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get system status: {str(e)}")


@router.post("/models/{model_id}/warmup")
async def warmup_model(
    request: Request,
    model_id: str,
) -> Dict[str, Any]:
    """
    Warm up a specific edge model for faster inference.
    
    This endpoint performs a dummy prediction to initialize the model
    and optimize memory layout for subsequent predictions.
    """
    try:
        edge_manager = request.app.state.edge_manager
        
        # Perform warmup prediction with dummy features
        dummy_features = [0.5] * 8  # 8 normalized features
        result = edge_manager.predict(model_id, dummy_features)
        
        logger.info("EDGE_MODEL_WARMUP_COMPLETED", model_id=model_id)
        
        return {
            'model_id': model_id,
            'status': 'warmed_up',
            'warmup_time_ms': result['inference_time_ms'],
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("EDGE_MODEL_WARMUP_ERROR", model_id=model_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Model warmup failed: {str(e)}")
