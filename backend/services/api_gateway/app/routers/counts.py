"""
Stock Count / Cycle Count API Endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
import httpx

from app.routers.auth import get_current_user
from app.dependencies.http import get_http_client

router = APIRouter(prefix="/counts", tags=["counts"])


class CountSubmitRequest(BaseModel):
    """Request to submit a stock count"""
    sku: str = Field(..., description="SKU/Article code")
    location: str = Field(..., description="Location/Bin where count was performed")
    counted_qty: float = Field(..., ge=0, description="Quantity counted")
    system_qty: float = Field(0, ge=0, description="System quantity (if known)")
    variance: float = Field(..., description="Variance (counted - system)")
    reason: Optional[str] = Field(None, description="Reason for variance")
    note: Optional[str] = Field(None, description="Additional notes")
    operation_id: str = Field(..., description="Idempotency key")


class CountRecord(BaseModel):
    """Stock count record"""
    id: str
    sku: str
    sku_name: str
    location: str
    counted_qty: float
    system_qty: float
    variance: float
    variance_pct: float
    reason: Optional[str]
    note: Optional[str]
    status: str  # pending, synced, reviewed
    counted_by: str
    counted_by_name: str
    created_at: str
    reviewed_at: Optional[str]
    reviewed_by: Optional[str]


class CountSummary(BaseModel):
    """Summary of stock counts"""
    total_counts: int
    total_variance: float
    positive_variance: float
    negative_variance: float
    counts_today: int
    pending_review: int
    top_variances: List[CountRecord]


@router.post("", response_model=dict, status_code=201)
async def submit_count(
    count_data: CountSubmitRequest,
    current_user: dict = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Submit a stock count
    
    - Accepts counts from workers
    - Stores in task_service (or dedicated count service)
    - Triggers variance alerts if threshold exceeded
    - Supports offline idempotency via operation_id
    """
    try:
        # For now, store in task_service audit log
        # In production, you might have a dedicated count_service
        audit_payload = {
            "action": "stock_count",
            "user_id": current_user.get("id"),
            "user_email": current_user.get("email"),
            "sku": count_data.sku,
            "location": count_data.location,
            "counted_qty": count_data.counted_qty,
            "system_qty": count_data.system_qty,
            "variance": count_data.variance,
            "reason": count_data.reason,
            "note": count_data.note,
            "operation_id": count_data.operation_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Store in task service audit (or create dedicated table)
        response = await http_client.post(
            "http://task-service:8001/api/audit",
            json=audit_payload,
            timeout=10.0,
        )
        response.raise_for_status()

        # Check variance threshold for alerts
        variance_pct = (
            abs(count_data.variance / count_data.system_qty * 100)
            if count_data.system_qty > 0
            else 0
        )

        # If variance > 10%, flag for review
        needs_review = variance_pct > 10 or abs(count_data.variance) > 100

        return {
            "message": "Count submitted successfully",
            "count_id": count_data.operation_id,
            "variance": count_data.variance,
            "variance_pct": round(variance_pct, 2),
            "needs_review": needs_review,
            "status": "pending" if needs_review else "synced",
        }

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.get("", response_model=List[CountRecord])
async def get_count_history(
    sku: Optional[str] = Query(None, description="Filter by SKU"),
    location: Optional[str] = Query(None, description="Filter by location"),
    from_date: Optional[str] = Query(None, description="From date (ISO)"),
    to_date: Optional[str] = Query(None, description="To date (ISO)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500, description="Max records"),
    current_user: dict = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Get count history
    
    - Returns counts submitted by worker or their team
    - Supports filtering by SKU, location, date, status
    """
    try:
        # Fetch from task service audit
        params = {
            "action": "stock_count",
            "limit": limit,
        }
        
        if current_user.get("role") == "magacioner":
            params["user_id"] = current_user.get("id")

        if sku:
            params["sku"] = sku
        if location:
            params["location"] = location
        if from_date:
            params["from_date"] = from_date
        if to_date:
            params["to_date"] = to_date

        response = await http_client.get(
            "http://task-service:8001/api/audit",
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        
        audit_records = response.json()

        # Transform to CountRecord format
        count_records = []
        for record in audit_records:
            variance_pct = (
                abs(record.get("variance", 0) / record.get("system_qty", 1) * 100)
                if record.get("system_qty", 0) > 0
                else 0
            )
            
            count_records.append(
                CountRecord(
                    id=record.get("id", record.get("operation_id")),
                    sku=record.get("sku", ""),
                    sku_name=record.get("sku_name", record.get("sku", "")),
                    location=record.get("location", ""),
                    counted_qty=record.get("counted_qty", 0),
                    system_qty=record.get("system_qty", 0),
                    variance=record.get("variance", 0),
                    variance_pct=round(variance_pct, 2),
                    reason=record.get("reason"),
                    note=record.get("note"),
                    status="synced",  # or "pending" based on needs_review logic
                    counted_by=record.get("user_id", ""),
                    counted_by_name=record.get("user_email", "").split("@")[0],
                    created_at=record.get("timestamp", datetime.utcnow().isoformat()),
                    reviewed_at=None,
                    reviewed_by=None,
                )
            )

        return count_records

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")


@router.get("/summary", response_model=CountSummary)
async def get_count_summary(
    from_date: Optional[str] = Query(None, description="From date (ISO)"),
    to_date: Optional[str] = Query(None, description="To date (ISO)"),
    current_user: dict = Depends(get_current_user),
    http_client: httpx.AsyncClient = Depends(get_http_client),
):
    """
    Get count summary for dashboard
    
    - Total counts, variances
    - Top variances by SKU/location
    - Counts pending review
    """
    # This would aggregate data from audit log or dedicated count tables
    # For now, return mock data structure
    return CountSummary(
        total_counts=0,
        total_variance=0.0,
        positive_variance=0.0,
        negative_variance=0.0,
        counts_today=0,
        pending_review=0,
        top_variances=[],
    )


# Moved exceptions to separate router - they will be accessible at /api/exceptions

