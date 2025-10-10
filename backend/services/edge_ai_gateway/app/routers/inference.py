from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app_common.logging import get_logger
from ..edge_ai_manager import EdgeInferenceRequest, InferenceType

logger = get_logger(__name__)
router = APIRouter()


class InferenceRequest(BaseModel):
    inference_type: str
    device_id: str
    warehouse_id: str
    input_data: Dict[str, Any]
    request_id: str = None


class InferenceResponse(BaseModel):
    request_id: str
    inference_type: str
    prediction: float
    confidence: float
    inference_time_ms: float
    model_version: str
    device_id: str
    timestamp: datetime
    recommendations: List[Dict[str, Any]]


@router.post("/edge/infer", response_model=InferenceResponse)
async def perform_edge_inference(
    request: Request,
    inference_request: InferenceRequest,
) -> InferenceResponse:
    """
    Perform edge AI inference with <100ms latency.
    
    This endpoint provides ultra-fast AI inference on edge devices
    for real-time decision making without backend connectivity.
    """
    try:
        # Get edge AI manager from app state
        edge_ai_manager = request.app.state.edge_ai_manager
        
        # Create inference request
        edge_request = EdgeInferenceRequest(
            inference_type=InferenceType(inference_request.inference_type),
            device_id=inference_request.device_id,
            warehouse_id=inference_request.warehouse_id,
            input_data=inference_request.input_data,
            timestamp=datetime.utcnow(),
            request_id=inference_request.request_id or f"edge_inf_{int(datetime.utcnow().timestamp() * 1000)}"
        )
        
        # Perform inference
        response = await edge_ai_manager.infer(edge_request)
        
        logger.info(
            "EDGE_INFERENCE_COMPLETED",
            request_id=edge_request.request_id,
            inference_type=inference_request.inference_type,
            inference_time_ms=response.inference_time_ms,
            confidence=response.confidence,
            device_id=inference_request.device_id
        )
        
        return InferenceResponse(
            request_id=response.request_id,
            inference_type=response.inference_type.value,
            prediction=response.prediction,
            confidence=response.confidence,
            inference_time_ms=response.inference_time_ms,
            model_version=response.model_version,
            device_id=response.device_id,
            timestamp=response.timestamp,
            recommendations=response.recommendations
        )
        
    except ValueError as e:
        logger.error("EDGE_INFERENCE_ERROR", error=str(e))
        raise HTTPException(status_code=400, detail=f"Invalid inference type: {str(e)}")
    
    except Exception as e:
        logger.error("EDGE_INFERENCE_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Edge inference failed: {str(e)}")


@router.post("/edge/batch-infer")
async def perform_batch_inference(
    request: Request,
    batch_requests: List[InferenceRequest],
) -> Dict[str, Any]:
    """
    Perform batch edge AI inference for multiple requests.
    
    Optimized for processing multiple inference requests simultaneously
    to maximize throughput on edge devices.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        # Process batch requests
        responses = []
        total_start_time = datetime.utcnow()
        
        for inference_request in batch_requests:
            # Create edge inference request
            edge_request = EdgeInferenceRequest(
                inference_type=InferenceType(inference_request.inference_type),
                device_id=inference_request.device_id,
                warehouse_id=inference_request.warehouse_id,
                input_data=inference_request.input_data,
                timestamp=datetime.utcnow(),
                request_id=inference_request.request_id or f"batch_inf_{int(datetime.utcnow().timestamp() * 1000)}"
            )
            
            # Perform inference
            response = await edge_ai_manager.infer(edge_request)
            
            responses.append({
                'request_id': response.request_id,
                'inference_type': response.inference_type.value,
                'prediction': response.prediction,
                'confidence': response.confidence,
                'inference_time_ms': response.inference_time_ms,
                'recommendations': response.recommendations
            })
        
        total_time = (datetime.utcnow() - total_start_time).total_seconds() * 1000
        
        logger.info(
            "EDGE_BATCH_INFERENCE_COMPLETED",
            batch_size=len(batch_requests),
            total_time_ms=total_time,
            average_time_ms=total_time / len(batch_requests)
        )
        
        return {
            'responses': responses,
            'batch_metrics': {
                'total_requests': len(batch_requests),
                'total_time_ms': total_time,
                'average_time_ms': total_time / len(batch_requests),
                'throughput_per_second': len(batch_requests) / (total_time / 1000)
            }
        }
        
    except Exception as e:
        logger.error("EDGE_BATCH_INFERENCE_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Batch inference failed: {str(e)}")


@router.get("/edge/inference-types")
async def get_inference_types() -> Dict[str, Any]:
    """
    Get available inference types for edge AI.
    
    Returns the list of supported inference types and their descriptions.
    """
    inference_types = {
        'worker_performance': {
            'description': 'Analyze worker performance and efficiency',
            'input_fields': ['current_tasks', 'completed_tasks', 'efficiency_score', 'idle_time', 'experience_level'],
            'output': 'Performance score and recommendations'
        },
        'task_optimization': {
            'description': 'Optimize task assignment and scheduling',
            'input_fields': ['task_complexity', 'priority', 'estimated_duration', 'worker_skill', 'current_load'],
            'output': 'Optimization score and task recommendations'
        },
        'load_balancing': {
            'description': 'Balance workload across workers and resources',
            'input_fields': ['worker_loads', 'task_queue', 'resource_availability', 'performance_history'],
            'output': 'Load balance score and redistribution recommendations'
        },
        'anomaly_detection': {
            'description': 'Detect anomalies in system behavior',
            'input_fields': ['system_metrics', 'event_patterns', 'performance_data', 'historical_baseline'],
            'output': 'Anomaly score and alert recommendations'
        },
        'resource_allocation': {
            'description': 'Optimize resource allocation and utilization',
            'input_fields': ['resource_usage', 'demand_forecast', 'capacity_constraints', 'cost_factors'],
            'output': 'Allocation score and resource recommendations'
        }
    }
    
    return {
        'inference_types': inference_types,
        'total_types': len(inference_types),
        'device_id': 'edge_device_12345'  # Mock device ID
    }
