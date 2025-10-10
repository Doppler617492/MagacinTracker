from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request

from app_common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/edge/status")
async def get_edge_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Get comprehensive edge device status.
    
    Returns device health, performance metrics, and system information
    for monitoring and diagnostics.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        # Get device status
        device_status = edge_ai_manager.get_device_status()
        
        # Get performance metrics
        performance_metrics = edge_ai_manager.get_performance_metrics()
        
        # Get model information
        model_info = edge_ai_manager.get_model_info()
        
        logger.info("EDGE_STATUS_REQUESTED")
        
        return {
            'device_status': device_status,
            'performance_metrics': performance_metrics,
            'model_info': model_info,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("EDGE_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get edge status: {str(e)}")


@router.get("/edge/health")
async def get_edge_health(
    request: Request,
) -> Dict[str, Any]:
    """
    Get edge device health status.
    
    Returns health indicators and system status for monitoring.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        device_status = edge_ai_manager.get_device_status()
        performance_metrics = edge_ai_manager.get_performance_metrics()
        
        # Determine overall health status
        health_status = 'healthy'
        health_issues = []
        
        # Check CPU usage
        if device_status['cpu_usage'] > 80:
            health_status = 'degraded'
            health_issues.append('High CPU usage')
        
        # Check memory usage
        if device_status['memory_usage'] > 85:
            health_status = 'degraded'
            health_issues.append('High memory usage')
        
        # Check temperature
        if device_status['temperature'] > 70:
            health_status = 'degraded'
            health_issues.append('High temperature')
        
        # Check battery level
        if device_status['battery_level'] < 20:
            health_status = 'degraded'
            health_issues.append('Low battery')
        
        # Check success rate
        if performance_metrics['success_rate'] < 0.95:
            health_status = 'degraded'
            health_issues.append('Low inference success rate')
        
        # Check inference time
        if performance_metrics['average_inference_time'] > 100:
            health_status = 'degraded'
            health_issues.append('Slow inference performance')
        
        health_metrics = {
            'status': health_status,
            'issues': health_issues,
            'device_id': device_status['device_id'],
            'uptime': '99.9%',  # Mock uptime
            'last_heartbeat': device_status['last_heartbeat'].isoformat(),
            'system_metrics': {
                'cpu_usage': device_status['cpu_usage'],
                'memory_usage': device_status['memory_usage'],
                'temperature': device_status['temperature'],
                'battery_level': device_status['battery_level']
            },
            'performance_metrics': {
                'total_inferences': performance_metrics['total_inferences'],
                'success_rate': performance_metrics['success_rate'],
                'average_inference_time': performance_metrics['average_inference_time']
            }
        }
        
        logger.info("EDGE_HEALTH_REQUESTED", status=health_status)
        
        return {
            'health_metrics': health_metrics,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("EDGE_HEALTH_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get edge health: {str(e)}")


@router.get("/edge/performance")
async def get_edge_performance(
    request: Request,
) -> Dict[str, Any]:
    """
    Get detailed edge performance metrics.
    
    Returns comprehensive performance statistics and trends.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        performance_metrics = edge_ai_manager.get_performance_metrics()
        device_status = edge_ai_manager.get_device_status()
        
        # Calculate performance indicators
        total_inferences = performance_metrics['total_inferences']
        success_rate = performance_metrics['success_rate']
        avg_inference_time = performance_metrics['average_inference_time']
        
        performance_indicators = {
            'inference_performance': {
                'total_inferences': total_inferences,
                'success_rate': success_rate,
                'average_inference_time_ms': avg_inference_time,
                'target_met': avg_inference_time < 100,  # Target: <100ms
                'performance_grade': 'A' if avg_inference_time < 50 else 'B' if avg_inference_time < 100 else 'C'
            },
            'system_performance': {
                'cpu_usage': device_status['cpu_usage'],
                'memory_usage': device_status['memory_usage'],
                'temperature': device_status['temperature'],
                'battery_level': device_status['battery_level'],
                'network_status': device_status['network_status']
            },
            'recent_activity': {
                'inference_history_size': performance_metrics['inference_history_size'],
                'recent_inferences': performance_metrics['recent_inferences'],
                'last_inference': performance_metrics['last_inference'].isoformat() if performance_metrics['last_inference'] else None
            }
        }
        
        logger.info("EDGE_PERFORMANCE_REQUESTED")
        
        return {
            'performance_indicators': performance_indicators,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("EDGE_PERFORMANCE_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get edge performance: {str(e)}")


@router.get("/edge/models")
async def get_edge_models(
    request: Request,
) -> Dict[str, Any]:
    """
    Get information about edge AI models.
    
    Returns model versions, training status, and performance metrics.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        model_info = edge_ai_manager.get_model_info()
        
        # Add model performance metrics
        model_performance = {
            'transformer': {
                **model_info['transformer'],
                'performance': {
                    'inference_count': edge_ai_manager.performance_metrics['total_inferences'],
                    'average_latency_ms': edge_ai_manager.performance_metrics['average_inference_time'],
                    'success_rate': edge_ai_manager.performance_metrics['success_rate'],
                    'model_size_kb': 2.5,  # Mock model size
                    'memory_usage_mb': 8.2  # Mock memory usage
                }
            },
            'yolo_lite': {
                **model_info['yolo_lite'],
                'performance': {
                    'detection_count': 0,  # Mock detection count
                    'average_latency_ms': 45.0,  # Mock latency
                    'accuracy': 0.92,  # Mock accuracy
                    'model_size_kb': 1.8,  # Mock model size
                    'memory_usage_mb': 5.1  # Mock memory usage
                }
            }
        }
        
        logger.info("EDGE_MODELS_REQUESTED")
        
        return {
            'models': model_performance,
            'total_models': len(model_performance),
            'device_id': edge_ai_manager.device_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("EDGE_MODELS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get edge models: {str(e)}")
