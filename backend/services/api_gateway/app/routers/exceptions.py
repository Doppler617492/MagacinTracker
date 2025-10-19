"""
Exception Reporting API Endpoints
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
import httpx

from app.routers.auth import get_current_user
from app.dependencies.http import get_http_client

router = APIRouter(prefix="/exceptions", tags=["exceptions"])


class ExceptionSubmitRequest(BaseModel):
    """Request to report an exception"""
    type: str = Field(..., description="Exception type: shortage, damage, mismatch, other")
    sku: str = Field(..., description="SKU/Article code")
    location: Optional[str] = Field(None, description="Location where exception occurred")
    description: str = Field(..., description="Description of the exception")
    operation_id: str = Field(..., description="Idempotency key")


@router.post("", response_model=dict, status_code=201)
async def submit_exception(
    exception_data: ExceptionSubmitRequest,
    current_user: dict = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Submit an exception report
    
    - Shortage, damage, mismatch, etc.
    - Stores in audit log
    - Triggers alerts
    """
    try:
        audit_payload = {
            "action": "exception_report",
            "user_id": current_user.get("id"),
            "user_email": current_user.get("email"),
            "exception_type": exception_data.type,
            "sku": exception_data.sku,
            "location": exception_data.location,
            "description": exception_data.description,
            "operation_id": exception_data.operation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        response = await http_client.post(
            "http://task-service:8001/api/audit",
            json=audit_payload,
            timeout=10.0,
        )
        response.raise_for_status()

        return {
            "message": "Exception reported successfully",
            "exception_id": exception_data.operation_id,
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")

