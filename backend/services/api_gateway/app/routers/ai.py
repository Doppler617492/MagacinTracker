from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from httpx import AsyncClient
from pydantic import BaseModel

from app_common.logging import get_logger
from ..services.auth import require_roles

from ..dependencies.http import get_task_client

logger = get_logger(__name__)
router = APIRouter()


class AIQueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None


class AIQueryResponse(BaseModel):
    answer: str
    data: Optional[Dict[str, Any]] = None
    chart_data: Optional[Dict[str, Any]] = None
    confidence: float
    query_id: str
    timestamp: datetime


class AIQueryContext(BaseModel):
    radnja_id: Optional[uuid.UUID] = None
    radnik_id: Optional[uuid.UUID] = None
    days: int = 7
    language: str = "sr"


async def interpret_natural_query(query: str, context: AIQueryContext) -> Dict[str, Any]:
    """
    Interpret natural language query and extract relevant KPI data.
    This is a simplified implementation - in production, you'd use OpenAI API or similar.
    """
    query_lower = query.lower()
    
    # Extract time period from query
    if "danas" in query_lower or "today" in query_lower:
        days = 1
    elif "juče" in query_lower or "yesterday" in query_lower:
        days = 1
    elif "sedmic" in query_lower or "week" in query_lower:
        days = 7
    elif "mesec" in query_lower or "month" in query_lower:
        days = 30
    else:
        days = context.days
    
    # Determine query type and required data
    if any(word in query_lower for word in ["najefikasniji", "najbolji", "top", "best", "efficient"]):
        query_type = "top_workers"
    elif any(word in query_lower for word in ["trend", "kretanje", "promena", "change"]):
        query_type = "daily_stats"
    elif any(word in query_lower for word in ["manual", "ručno", "skeniranje", "scanning"]):
        query_type = "manual_completion"
    elif any(word in query_lower for word in ["ukupno", "total", "broj", "count"]):
        query_type = "summary"
    else:
        query_type = "summary"  # Default to summary
    
    return {
        "query_type": query_type,
        "days": days,
        "extracted_filters": {
            "radnja_id": context.radnja_id,
            "radnik_id": context.radnik_id,
            "days": days
        }
    }


async def generate_ai_response(
    query: str, 
    query_type: str, 
    data: Dict[str, Any], 
    context: AIQueryContext
) -> Dict[str, Any]:
    """
    Generate AI response based on query type and data.
    This is a simplified implementation - in production, you'd use OpenAI API.
    """
    
    if query_type == "top_workers":
        workers = data.get("data", [])
        if not workers:
            return {
                "answer": "Nema dostupnih podataka o radnicima za odabrani period.",
                "confidence": 0.8
            }
        
        top_worker = workers[0] if workers else None
        if top_worker:
            answer = f"Najefikasniji radnik u poslednje {context.days} dana je {top_worker.get('worker_name', 'Nepoznat')} sa {top_worker.get('completed_tasks', 0)} završenih zadataka."
        else:
            answer = "Nema dostupnih podataka o performansama radnika."
        
        return {
            "answer": answer,
            "data": data,
            "chart_data": {
                "type": "bar",
                "data": workers[:5],  # Top 5 workers
                "x_field": "worker_name",
                "y_field": "completed_tasks"
            },
            "confidence": 0.9
        }
    
    elif query_type == "daily_stats":
        daily_data = data.get("data", [])
        if not daily_data:
            return {
                "answer": "Nema dostupnih podataka o dnevnim trendovima za odabrani period.",
                "confidence": 0.8
            }
        
        # Calculate trend
        if len(daily_data) >= 2:
            recent_avg = sum(item.get("value", 0) for item in daily_data[-3:]) / min(3, len(daily_data))
            older_avg = sum(item.get("value", 0) for item in daily_data[:3]) / min(3, len(daily_data))
            trend = "rastući" if recent_avg > older_avg else "opadajući" if recent_avg < older_avg else "stabilan"
        else:
            trend = "nedovoljno podataka"
        
        total_items = sum(item.get("value", 0) for item in daily_data)
        answer = f"U poslednje {context.days} dana je obrađeno ukupno {total_items} stavki. Trend je {trend}."
        
        return {
            "answer": answer,
            "data": data,
            "chart_data": {
                "type": "line",
                "data": daily_data,
                "x_field": "date",
                "y_field": "value"
            },
            "confidence": 0.85
        }
    
    elif query_type == "manual_completion":
        manual_data = data.get("data", [])
        summary = data.get("summary", {})
        
        if not manual_data:
            return {
                "answer": "Nema dostupnih podataka o ručnim potvrdama i skeniranju.",
                "confidence": 0.8
            }
        
        scanned_items = summary.get("scanned_items", 0)
        manual_items = summary.get("manual_items", 0)
        total = scanned_items + manual_items
        
        if total > 0:
            manual_percentage = (manual_items / total) * 100
            scanned_percentage = (scanned_items / total) * 100
            
            answer = f"Od ukupno {total} stavki, {scanned_items} ({scanned_percentage:.1f}%) je skenirano, a {manual_items} ({manual_percentage:.1f}%) je ručno potvrđeno."
        else:
            answer = "Nema dostupnih podataka o načinu potvrde stavki."
        
        return {
            "answer": answer,
            "data": data,
            "chart_data": {
                "type": "pie",
                "data": manual_data,
                "angle_field": "value",
                "color_field": "type"
            },
            "confidence": 0.9
        }
    
    else:  # summary
        summary = data.get("summary", {})
        total_items = summary.get("total_items", 0)
        manual_percentage = summary.get("manual_percentage", 0)
        avg_time = summary.get("avg_time_per_task", 0)
        
        answer = f"Ukupno je obrađeno {total_items} stavki. {manual_percentage:.1f}% je ručno potvrđeno, a prosečno vreme po zadatku je {avg_time:.1f} minuta."
        
        return {
            "answer": answer,
            "data": data,
            "confidence": 0.8
        }


@router.post("/query", response_model=AIQueryResponse)
async def process_ai_query(
    request: Request,
    query_request: AIQueryRequest,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> AIQueryResponse:
    """
    Process natural language query about KPI data and return AI-generated response.
    """
    query_id = str(uuid.uuid4())
    start_time = datetime.utcnow()
    
    try:
        # Parse context from request
        context_data = query_request.context or {}
        context = AIQueryContext(**context_data)
        
        # Interpret the natural language query
        interpretation = await interpret_natural_query(query_request.query, context)
        query_type = interpretation["query_type"]
        filters = interpretation["extracted_filters"]
        
        # Fetch relevant KPI data based on query type
        if query_type == "top_workers":
            response = await task_client.get("/api/kpi/top-workers", params=filters)
        elif query_type == "daily_stats":
            response = await task_client.get("/api/kpi/daily-stats", params=filters)
        elif query_type == "manual_completion":
            response = await task_client.get("/api/kpi/manual-completion", params=filters)
        else:  # summary
            response = await task_client.get("/api/kpi/summary", params=filters)
        
        response.raise_for_status()
        kpi_data = response.json()
        
        # Generate AI response
        ai_response = await generate_ai_response(
            query_request.query, 
            query_type, 
            kpi_data, 
            context
        )
        
        # Calculate processing time
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log the AI query for audit
        logger.info(
            "AI_QUERY_EXECUTED",
            query_id=query_id,
            query=query_request.query,
            query_type=query_type,
            processing_time_ms=processing_time * 1000,
            confidence=ai_response["confidence"],
            user_id=getattr(request.state, "user_id", "unknown")
        )
        
        return AIQueryResponse(
            answer=ai_response["answer"],
            data=ai_response.get("data"),
            chart_data=ai_response.get("chart_data"),
            confidence=ai_response["confidence"],
            query_id=query_id,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(
            "AI_QUERY_ERROR",
            query_id=query_id,
            query=query_request.query,
            error=str(e),
            user_id=getattr(request.state, "user_id", "unknown")
        )
        raise HTTPException(status_code=500, detail=f"Greška pri obradi AI upita: {str(e)}")


@router.get("/suggestions")
async def get_query_suggestions(
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, List[str]]:
    """
    Get suggested queries for the AI assistant.
    """
    return {
        "suggestions": [
            "Ko je bio najefikasniji radnik prošle sedmice?",
            "Kakav je trend obrade stavki u poslednje 30 dana?",
            "Koliko je procenat ručnih potvrda?",
            "Koji radnik ima najviše završenih zadataka?",
            "Kako se menja broj stavki dnevno?",
            "Uporedi skeniranje i ručne potvrde",
            "Ukupno stanje za danas",
            "Najbolji performeri ovog meseca"
        ],
        "categories": {
            "performanse": ["najefikasniji", "najbolji", "top radnici"],
            "trendovi": ["kretanje", "promena", "rast", "pad"],
            "statistike": ["ukupno", "procenat", "prosek", "broj"],
            "poređenja": ["uporedi", "razlika", "više", "manje"]
        }
    }


@router.get("/history")
async def get_query_history(
    limit: int = 10,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """
    Get recent AI query history (simplified - in production, store in database).
    """
    # This is a simplified implementation
    # In production, you'd query a database for actual query history
    return {
        "history": [
            {
                "query": "Ko je bio najefikasniji radnik prošle sedmice?",
                "answer": "Najefikasniji radnik je Marko Šef sa 45 završenih zadataka.",
                "timestamp": datetime.utcnow() - timedelta(hours=2),
                "confidence": 0.9
            },
            {
                "query": "Kakav je trend obrade stavki?",
                "answer": "Trend je rastući sa prosečno 120 stavki dnevno.",
                "timestamp": datetime.utcnow() - timedelta(hours=5),
                "confidence": 0.85
            }
        ],
        "total": 2
    }


# AI Recommendations endpoints (proxy to task service)
@router.post("/recommendations")
async def get_ai_recommendations(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["sef", "menadzer"])),
) -> List[Dict[str, Any]]:
    """Get AI recommendations for operational optimization."""
    # Forward the Authorization header from the original request
    auth_header = request.headers.get("Authorization")
    headers = {}
    if auth_header:
        headers["Authorization"] = auth_header
        
    response = await task_client.post("/api/ai/recommendations", headers=headers)
    response.raise_for_status()
    return response.json()


@router.post("/load-balance")
async def simulate_load_balance(
    request: Request,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["sef", "menadzer"])),
) -> Dict[str, Any]:
    """Simulate load balance scenario."""
    body = await request.body()
    response = await task_client.post(
        "/api/ai/load-balance",
        content=body,
        headers={"content-type": "application/json"}
    )
    response.raise_for_status()
    return response.json()


@router.post("/recommendations/{recommendation_id}/apply")
async def apply_recommendation(
    request: Request,
    recommendation_id: str,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Apply an AI recommendation."""
    response = await task_client.post(f"/api/ai/recommendations/{recommendation_id}/apply")
    response.raise_for_status()
    return response.json()


@router.post("/recommendations/{recommendation_id}/dismiss")
async def dismiss_recommendation(
    request: Request,
    recommendation_id: str,
    task_client: AsyncClient = Depends(get_task_client),
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Dismiss an AI recommendation."""
    response = await task_client.post(f"/api/ai/recommendations/{recommendation_id}/dismiss")
    response.raise_for_status()
    return response.json()
