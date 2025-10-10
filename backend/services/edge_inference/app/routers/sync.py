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
    models_updated: int
    sync_duration_ms: float
    global_model_version: int
    sync_time: str
    error: str = None


@router.post("/sync", response_model=SyncResponse)
async def sync_with_hub(
    request: Request,
    sync_request: SyncRequest,
) -> SyncResponse:
    """
    Synchronize edge models with the central AI hub.
    
    This endpoint fetches the latest global model from the hub
    and updates all edge models with the new parameters.
    """
    try:
        edge_manager = request.app.state.edge_manager
        
        # Check if sync is needed or forced
        if not sync_request.force and not edge_manager.should_sync():
            return SyncResponse(
                status="not_needed",
                models_updated=0,
                sync_duration_ms=0,
                global_model_version=0,
                sync_time=datetime.utcnow().isoformat()
            )
        
        # Perform synchronization
        result = await edge_manager.sync_with_hub()
        
        logger.info("EDGE_SYNC_COMPLETED", result=result)
        
        return SyncResponse(
            status=result['status'],
            models_updated=result.get('models_updated', 0),
            sync_duration_ms=result.get('sync_duration_ms', 0),
            global_model_version=result.get('global_model_version', 0),
            sync_time=result.get('sync_time', datetime.utcnow().isoformat()),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error("EDGE_SYNC_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/sync/status")
async def get_sync_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Get current synchronization status.
    
    Returns information about last sync time, sync frequency,
    and whether sync is needed or in progress.
    """
    try:
        edge_manager = request.app.state.edge_manager
        
        status = {
            'last_sync': edge_manager.last_sync.isoformat() if edge_manager.last_sync else None,
            'sync_interval_minutes': edge_manager.sync_interval.total_seconds() / 60,
            'should_sync': edge_manager.should_sync(),
            'sync_running': edge_manager.sync_running,
            'sync_errors': edge_manager.sync_errors,
            'total_predictions': edge_manager.total_predictions
        }
        
        logger.info("EDGE_SYNC_STATUS_REQUESTED")
        
        return status
        
    except Exception as e:
        logger.error("EDGE_SYNC_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get sync status: {str(e)}")


@router.post("/sync/force")
async def force_sync(
    request: Request,
) -> SyncResponse:
    """
    Force immediate synchronization with the AI hub.
    
    This endpoint bypasses the normal sync schedule and immediately
    synchronizes all edge models with the latest global model.
    """
    try:
        edge_manager = request.app.state.edge_manager
        
        # Force synchronization
        result = await edge_manager.sync_with_hub()
        
        logger.info("EDGE_FORCE_SYNC_COMPLETED", result=result)
        
        return SyncResponse(
            status=result['status'],
            models_updated=result.get('models_updated', 0),
            sync_duration_ms=result.get('sync_duration_ms', 0),
            global_model_version=result.get('global_model_version', 0),
            sync_time=result.get('sync_time', datetime.utcnow().isoformat()),
            error=result.get('error')
        )
        
    except Exception as e:
        logger.error("EDGE_FORCE_SYNC_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Force sync failed: {str(e)}")


@router.get("/hub/status")
async def get_hub_status(
    request: Request,
) -> Dict[str, Any]:
    """
    Check the status of the central AI hub.
    
    This endpoint attempts to connect to the hub and returns
    its availability and current model version.
    """
    try:
        edge_manager = request.app.state.edge_manager
        
        # Try to get hub status
        import aiohttp
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{edge_manager.hub_url}/api/health", timeout=5) as response:
                    if response.status == 200:
                        hub_data = await response.json()
                        
                        return {
                            'hub_available': True,
                            'hub_status': hub_data.get('status', 'unknown'),
                            'hub_version': hub_data.get('version', 'unknown'),
                            'hub_url': edge_manager.hub_url,
                            'check_time': datetime.utcnow().isoformat()
                        }
                    else:
                        return {
                            'hub_available': False,
                            'hub_status': f'HTTP {response.status}',
                            'hub_url': edge_manager.hub_url,
                            'check_time': datetime.utcnow().isoformat()
                        }
            except asyncio.TimeoutError:
                return {
                    'hub_available': False,
                    'hub_status': 'timeout',
                    'hub_url': edge_manager.hub_url,
                    'check_time': datetime.utcnow().isoformat()
                }
            except Exception as e:
                return {
                    'hub_available': False,
                    'hub_status': f'error: {str(e)}',
                    'hub_url': edge_manager.hub_url,
                    'check_time': datetime.utcnow().isoformat()
                }
        
    except Exception as e:
        logger.error("EDGE_HUB_STATUS_ERROR", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to check hub status: {str(e)}")
