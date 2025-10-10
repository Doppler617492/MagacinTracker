from __future__ import annotations

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app_common.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class SyncRequest(BaseModel):
    force: bool = False


class SyncResponse(BaseModel):
    status: str
    sync_duration_ms: float
    model_version: str
    sync_time: str
    error: str = None


@router.post("/edge/sync", response_model=SyncResponse)
async def sync_with_hub(
    request: Request,
    sync_request: SyncRequest,
) -> SyncResponse:
    """
    Synchronize edge AI models with the central AI hub.
    
    This endpoint fetches the latest AI models from the hub
    and updates the edge device with new model parameters.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        # Check if sync is needed or forced
        if not sync_request.force and not edge_ai_manager.should_sync():
            return SyncResponse(
                status="not_needed",
                sync_duration_ms=0,
                model_version=edge_ai_manager.tiny_transformer.model_version,
                sync_time=datetime.utcnow().isoformat()
            )
        
        # Perform synchronization
        result = await edge_ai_manager.sync_with_hub()
        
        logger.info("EDGE_SYNC_COMPLETED", result=result)
        
        return SyncResponse(
            status=result['status'],
            sync_duration_ms=result.get('sync_duration_ms', 0),
            model_version=result.get('model_version', edge_ai_manager.tiny_transformer.model_version),
            sync_time=result.get('sync_time', datetime.utcnow().isoformat()),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error("EDGE_SYNC_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/edge/sync/status")
async def get_sync_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Get current synchronization status.
    
    Returns information about last sync time, sync frequency,
    and whether sync is needed or in progress.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        status = {
            'last_sync': edge_ai_manager.last_sync.isoformat() if edge_ai_manager.last_sync else None,
            'sync_interval_minutes': edge_ai_manager.sync_interval.total_seconds() / 60,
            'should_sync': edge_ai_manager.should_sync(),
            'sync_running': edge_ai_manager.sync_running,
            'device_id': edge_ai_manager.device_id,
            'current_model_version': edge_ai_manager.tiny_transformer.model_version
        }
        
        logger.info("EDGE_SYNC_STATUS_REQUESTED")
        
        return status
        
    except Exception as e:
        logger.error("EDGE_SYNC_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.post("/edge/sync/force")
async def force_sync(
    request: Request,
) -> SyncResponse:
    """
    Force immediate synchronization with the AI hub.
    
    This endpoint bypasses the normal sync schedule and immediately
    synchronizes the edge device with the latest models from the hub.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        # Force synchronization
        result = await edge_ai_manager.sync_with_hub()
        
        logger.info("EDGE_FORCE_SYNC_COMPLETED", result=result)
        
        return SyncResponse(
            status=result['status'],
            sync_duration_ms=result.get('sync_duration_ms', 0),
            model_version=result.get('model_version', edge_ai_manager.tiny_transformer.model_version),
            sync_time=result.get('sync_time', datetime.utcnow().isoformat()),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error("EDGE_FORCE_SYNC_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Force sync failed: {str(e)}")


@router.get("/edge/hub/status")
async def get_hub_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Check the status of the central AI hub.
    
    This endpoint attempts to connect to the hub and returns
    its availability and current model version.
    """
    try:
        edge_ai_manager = request.app.state.edge_ai_manager
        
        # Try to get hub status
        # In production, this would make an actual HTTP request to the hub
        try:
            # Mock hub status check
            await asyncio.sleep(0.1)  # Simulate network delay
            
            hub_status = {
                'hub_available': True,
                'hub_status': 'healthy',
                'hub_version': 'v0.9.0',
                'hub_url': edge_ai_manager.hub_url,
                'model_version_available': '1.0.123',
                'check_time': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            hub_status = {
                'hub_available': False,
                'hub_status': f'error: {str(e)}',
                'hub_url': edge_ai_manager.hub_url,
                'check_time': datetime.utcnow().isoformat()
            }
        
        return hub_status
        
    except Exception as e:
        logger.error("EDGE_HUB_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check hub status: {str(e)}")
