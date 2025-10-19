"""
Stream events and metrics endpoints.
Provides real-time insights into system activity and performance.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
from uuid import UUID
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app_common.db import get_db
from app_common.config import get_settings
from app_common.logging import get_logger
from ..models import Trebovanje, TrebovanjeStavka, Zaduznica, UserAccount, ScanLog
from ..models.enums import Role, TrebovanjeStatus, ZaduznicaStatus

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


async def get_any_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> dict:
    """Get user from JWT token - accepts both device tokens and regular user tokens"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        role: str = payload.get("role")
        if user_id is None:
            raise credentials_exception
    except JWTError as exc:  # noqa: BLE001
        raise credentials_exception from exc
    
    # Check if this is a device token (non-UUID format)
    try:
        uuid.UUID(user_id)
        is_device = False
    except ValueError:
        is_device = True
    
    # For device tokens, just validate the role
    if is_device:
        if role not in ["MENADZER", "ADMIN", "SEF"]:
            raise credentials_exception
        return {
            "id": user_id,
            "role": role,
            "device_id": user_id,
        }
    
    # For regular user tokens, look up in database
    result = await db.execute(
        text("SELECT id, email, first_name, last_name, role, is_active FROM users WHERE id = :user_id"),
        {"user_id": user_id}
    )
    user_row = result.fetchone()
    
    if user_row is None or not user_row.is_active:
        raise credentials_exception
    
    return {
        "id": str(user_row.id),
        "email": user_row.email,
        "first_name": user_row.first_name,
        "last_name": user_row.last_name,
        "role": user_row.role,
    }


@router.get("/stream/events/recent")
async def get_recent_events(
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get recent system events from scan logs and task updates."""
    
    # Get recent scan events
    from ..models import ZaduznicaStavka
    
    scan_stmt = (
        select(
            ScanLog.id,
            ScanLog.barcode,
            ScanLog.created_at,
            ScanLog.zaduznica_stavka_id,
            ZaduznicaStavka.zaduznica_id,
            UserAccount.first_name,
            UserAccount.last_name,
        )
        .join(ZaduznicaStavka, ScanLog.zaduznica_stavka_id == ZaduznicaStavka.id)
        .join(Zaduznica, ZaduznicaStavka.zaduznica_id == Zaduznica.id)
        .join(UserAccount, ScanLog.user_id == UserAccount.id)
        .order_by(ScanLog.created_at.desc())
        .limit(limit)
    )
    
    scan_result = await db.execute(scan_stmt)
    scans = scan_result.all()
    
    events = []
    for scan in scans:
        events.append({
            "event_id": str(scan.id),
            "event_type": "SCAN_EVENT",
            "timestamp": scan.created_at.isoformat() if scan.created_at else datetime.now(timezone.utc).isoformat(),
            "worker": f"{scan.first_name} {scan.last_name}",
            "data": {
                "barcode": scan.barcode,
                "zaduznica_stavka_id": str(scan.zaduznica_stavka_id),
                "zaduznica_id": str(scan.zaduznica_id),
            }
        })
    
    return {
        "events": events,
        "total_count": len(events),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stream/events/worker-activity")
async def get_worker_activity(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get current worker activity metrics."""
    
    # Get workers with active tasks (assigned or in progress)
    stmt = (
        select(
            UserAccount.id,
            UserAccount.first_name,
            UserAccount.last_name,
            func.count(Zaduznica.id).label("active_tasks"),
            func.count(ScanLog.id).label("scans_today"),
        )
        .join(Zaduznica, UserAccount.id == Zaduznica.magacioner_id, isouter=True)
        .join(ScanLog, UserAccount.id == ScanLog.user_id, isouter=True)
        .where(UserAccount.role == Role.MAGACIONER)
        .where(
            (Zaduznica.status.in_([ZaduznicaStatus.assigned, ZaduznicaStatus.in_progress])) |
            (Zaduznica.id.is_(None))
        )
        .where(
            (ScanLog.created_at >= datetime.now(timezone.utc) - timedelta(days=1)) |
            (ScanLog.id.is_(None))
        )
        .group_by(UserAccount.id, UserAccount.first_name, UserAccount.last_name)
    )
    
    result = await db.execute(stmt)
    workers = result.all()
    
    worker_activity = {}
    for worker in workers:
        worker_id = str(worker.id)
        worker_activity[worker_id] = {
            "name": f"{worker.first_name} {worker.last_name}",
            "active_tasks": worker.active_tasks or 0,
            "scans_today": worker.scans_today or 0,
            "status": "active" if worker.active_tasks > 0 else "idle"
        }
    
    return {
        "worker_activity": worker_activity,
        "total_workers": len(workers),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stream/events/warehouse-load")
async def get_warehouse_load(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get current warehouse load metrics by location."""
    
    # Get trebovanja grouped by radnja (warehouse/store) using raw SQL for simplicity
    warehouse_stmt = text("""
        SELECT 
            r.naziv as warehouse_name,
            COUNT(t.id) as total_tasks,
            COUNT(CASE WHEN t.status = 'assigned' THEN 1 END) as pending_tasks,
            COUNT(CASE WHEN t.status = 'in_progress' THEN 1 END) as in_progress_tasks,
            COUNT(CASE WHEN t.status = 'done' THEN 1 END) as completed_tasks
        FROM trebovanje t
        JOIN radnja r ON t.radnja_id = r.id
        WHERE t.created_at >= :cutoff
        GROUP BY r.naziv
    """)
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(warehouse_stmt, {"cutoff": cutoff})
    warehouses = result.all()
    
    warehouse_load = {}
    for wh in warehouses:
        total = wh.total_tasks or 1
        active = (wh.pending_tasks or 0) + (wh.in_progress_tasks or 0)
        warehouse_load[wh.warehouse_name or "Unknown"] = {
            "total_tasks": wh.total_tasks or 0,
            "pending": wh.pending_tasks or 0,
            "in_progress": wh.in_progress_tasks or 0,
            "completed": wh.completed_tasks or 0,
            "load_percentage": round(active / total * 100, 1) if total > 0 else 0
        }
    
    return {
        "warehouse_load": warehouse_load,
        "total_warehouses": len(warehouses),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stream/metrics")
async def get_stream_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get overall stream processing metrics."""
    
    # Count events from today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    scan_count_stmt = select(func.count(ScanLog.id)).where(ScanLog.created_at >= today_start)
    scan_count_result = await db.execute(scan_count_stmt)
    event_count = scan_count_result.scalar() or 0
    
    # Get active connections (workers with recent activity)
    active_workers_stmt = (
        select(func.count(func.distinct(Zaduznica.magacioner_id)))
        .where(Zaduznica.status.in_([ZaduznicaStatus.assigned, ZaduznicaStatus.in_progress]))
    )
    active_result = await db.execute(active_workers_stmt)
    active_connections = active_result.scalar() or 0
    
    # Calculate events per second (rough estimate for last hour)
    hours_today = (datetime.now(timezone.utc) - today_start).total_seconds() / 3600
    events_per_second = round(event_count / max(hours_today * 3600, 1), 2)
    
    metrics = {
        "event_count": event_count,
        "average_latency_ms": 12.5,  # Mock value - would need actual tracking
        "events_per_second": events_per_second,
        "error_rate": 0.001,  # Mock value
        "active_connections": active_connections
    }
    
    return {
        "metrics": metrics,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "task-service-stream"
    }


@router.get("/stream/metrics/throughput")
async def get_throughput_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get throughput-specific metrics."""
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get scan counts for last 24 hours by hour
    hourly_stmt = text("""
        SELECT 
            date_trunc('hour', created_at) as hour,
            COUNT(*) as scan_count
        FROM scanlog
        WHERE created_at >= :today_start
        GROUP BY hour
        ORDER BY hour DESC
        LIMIT 24
    """)
    
    hourly_result = await db.execute(hourly_stmt, {"today_start": today_start})
    hourly_data = hourly_result.all()
    
    throughput_by_hour = [
        {
            "hour": row.hour.isoformat() if row.hour else datetime.now(timezone.utc).isoformat(),
            "events": row.scan_count
        }
        for row in hourly_data
    ]
    
    total_events = sum(row.scan_count for row in hourly_data)
    avg_per_hour = round(total_events / max(len(hourly_data), 1), 2)
    
    throughput_metrics = {
        "events_per_second": round(avg_per_hour / 3600, 2),
        "events_per_hour": avg_per_hour,
        "total_events_24h": total_events,
        "hourly_breakdown": throughput_by_hour,
        "peak_hour": max(throughput_by_hour, key=lambda x: x["events"]) if throughput_by_hour else None
    }
    
    return {
        "throughput_metrics": throughput_metrics,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stream/metrics/performance")
async def get_performance_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get performance metrics."""
    
    # Get average task completion time
    completion_stmt = text("""
        SELECT 
            AVG(EXTRACT(EPOCH FROM (closed_at - created_at))) as avg_completion_seconds,
            COUNT(*) as completed_count
        FROM trebovanje
        WHERE status = 'done' 
        AND closed_at >= :cutoff
    """)
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    completion_result = await db.execute(completion_stmt, {"cutoff": cutoff})
    completion_data = completion_result.fetchone()
    
    avg_completion_time = completion_data.avg_completion_seconds if completion_data and completion_data.avg_completion_seconds else 0
    
    performance_metrics = {
        "average_processing_time_ms": round(avg_completion_time * 1000, 2),
        "average_task_completion_seconds": round(avg_completion_time, 2),
        "completed_tasks_7d": completion_data.completed_count if completion_data else 0,
        "system_uptime_hours": 24,  # Mock value
        "cpu_usage_percent": 45.2,  # Mock value
        "memory_usage_percent": 62.8,  # Mock value
    }
    
    return {
        "performance_metrics": performance_metrics,
        "raw_metrics": {
            "event_count": completion_data.completed_count if completion_data else 0,
            "average_latency_ms": round(avg_completion_time * 1000, 2),
            "events_per_second": 0.5,
            "error_rate": 0.001,
            "active_connections": 3
        },
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@router.get("/stream/metrics/health")
async def get_health_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_any_user),
) -> Dict[str, Any]:
    """Get system health metrics."""
    
    # Check database connectivity
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception:
        db_status = "unhealthy"
    
    # Get error counts (mock for now)
    health_metrics = {
        "overall_status": "healthy" if db_status == "healthy" else "degraded",
        "database_status": db_status,
        "redis_status": "healthy",  # Mock value
        "api_response_time_ms": 125.5,  # Mock value
        "error_rate_percent": 0.1,  # Mock value
        "warnings_count": 0,
        "errors_count": 0,
        "last_check": datetime.now(timezone.utc).isoformat()
    }
    
    return {
        "health_metrics": health_metrics,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

