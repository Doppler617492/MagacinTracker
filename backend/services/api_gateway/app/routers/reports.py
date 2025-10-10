from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from httpx import AsyncClient
from pydantic import BaseModel, Field

from app_common.logging import get_logger
from ..services.auth import require_roles

from ..dependencies.http import get_task_client

logger = get_logger(__name__)
router = APIRouter()


class ReportChannel(str, Enum):
    email = "email"
    slack = "slack"
    both = "both"


class ReportFrequency(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class ReportScheduleCreate(BaseModel):
    name: str = Field(..., description="Report schedule name")
    description: Optional[str] = Field(None, description="Report description")
    channel: ReportChannel = Field(..., description="Delivery channel")
    frequency: ReportFrequency = Field(..., description="Report frequency")
    recipients: List[str] = Field(..., description="Email addresses or Slack channels")
    filters: Dict[str, Any] = Field(default_factory=dict, description="KPI filters")
    enabled: bool = Field(True, description="Whether the schedule is active")
    time_hour: int = Field(7, ge=0, le=23, description="Hour to send report (0-23)")
    time_minute: int = Field(0, ge=0, le=59, description="Minute to send report (0-59)")


class ReportScheduleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    channel: Optional[ReportChannel] = None
    frequency: Optional[ReportFrequency] = None
    recipients: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None
    enabled: Optional[bool] = None
    time_hour: Optional[int] = Field(None, ge=0, le=23)
    time_minute: Optional[int] = Field(None, ge=0, le=59)


class ReportSchedule(BaseModel):
    id: str
    name: str
    description: Optional[str]
    channel: ReportChannel
    frequency: ReportFrequency
    recipients: List[str]
    filters: Dict[str, Any]
    enabled: bool
    time_hour: int
    time_minute: int
    created_at: datetime
    updated_at: datetime
    last_sent: Optional[datetime]
    next_send: Optional[datetime]
    total_sent: int
    total_failed: int


class ReportRunRequest(BaseModel):
    schedule_id: str
    recipients: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None


# In-memory storage for demo (in production, use database)
report_schedules: Dict[str, ReportSchedule] = {}


def calculate_next_send(frequency: ReportFrequency, time_hour: int, time_minute: int) -> datetime:
    """Calculate next send time based on frequency and time."""
    now = datetime.now()
    target_time = now.replace(hour=time_hour, minute=time_minute, second=0, microsecond=0)
    
    if frequency == ReportFrequency.daily:
        if target_time <= now:
            target_time += timedelta(days=1)
    elif frequency == ReportFrequency.weekly:
        # Next Monday at specified time
        days_ahead = 7 - now.weekday()  # Monday is 0
        if days_ahead == 7:  # Today is Monday
            if target_time <= now:
                days_ahead = 7
        target_time += timedelta(days=days_ahead)
    elif frequency == ReportFrequency.monthly:
        # First day of next month
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1, hour=time_hour, minute=time_minute)
        else:
            next_month = now.replace(month=now.month + 1, day=1, hour=time_hour, minute=time_minute)
        target_time = next_month
    
    return target_time


@router.post("/schedules", response_model=ReportSchedule)
async def create_report_schedule(
    request: Request,
    schedule_data: ReportScheduleCreate,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> ReportSchedule:
    """Create a new report schedule."""
    schedule_id = str(uuid.uuid4())
    now = datetime.utcnow()
    next_send = calculate_next_send(schedule_data.frequency, schedule_data.time_hour, schedule_data.time_minute)
    
    schedule = ReportSchedule(
        id=schedule_id,
        name=schedule_data.name,
        description=schedule_data.description,
        channel=schedule_data.channel,
        frequency=schedule_data.frequency,
        recipients=schedule_data.recipients,
        filters=schedule_data.filters,
        enabled=schedule_data.enabled,
        time_hour=schedule_data.time_hour,
        time_minute=schedule_data.time_minute,
        created_at=now,
        updated_at=now,
        last_sent=None,
        next_send=next_send,
        total_sent=0,
        total_failed=0
    )
    
    report_schedules[schedule_id] = schedule
    
    logger.info(
        "REPORT_SCHEDULED",
        schedule_id=schedule_id,
        name=schedule_data.name,
        channel=schedule_data.channel,
        frequency=schedule_data.frequency,
        recipients=schedule_data.recipients,
        user_id=getattr(request.state, "user_id", "unknown")
    )
    
    return schedule


@router.get("/schedules", response_model=List[ReportSchedule])
async def get_report_schedules(
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> List[ReportSchedule]:
    """Get all report schedules."""
    return list(report_schedules.values())


@router.get("/schedules/{schedule_id}", response_model=ReportSchedule)
async def get_report_schedule(
    schedule_id: str,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> ReportSchedule:
    """Get a specific report schedule."""
    if schedule_id not in report_schedules:
        raise HTTPException(status_code=404, detail="Report schedule not found")
    
    return report_schedules[schedule_id]


@router.patch("/schedules/{schedule_id}", response_model=ReportSchedule)
async def update_report_schedule(
    request: Request,
    schedule_id: str,
    update_data: ReportScheduleUpdate,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> ReportSchedule:
    """Update a report schedule."""
    if schedule_id not in report_schedules:
        raise HTTPException(status_code=404, detail="Report schedule not found")
    
    schedule = report_schedules[schedule_id]
    update_dict = update_data.dict(exclude_unset=True)
    
    # Update fields
    for field, value in update_dict.items():
        setattr(schedule, field, value)
    
    # Recalculate next send time if frequency or time changed
    if "frequency" in update_dict or "time_hour" in update_dict or "time_minute" in update_dict:
        schedule.next_send = calculate_next_send(schedule.frequency, schedule.time_hour, schedule.time_minute)
    
    schedule.updated_at = datetime.utcnow()
    
    logger.info(
        "REPORT_SCHEDULE_UPDATED",
        schedule_id=schedule_id,
        updates=update_dict,
        user_id=getattr(request.state, "user_id", "unknown")
    )
    
    return schedule


@router.delete("/schedules/{schedule_id}")
async def delete_report_schedule(
    request: Request,
    schedule_id: str,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, str]:
    """Delete a report schedule."""
    if schedule_id not in report_schedules:
        raise HTTPException(status_code=404, detail="Report schedule not found")
    
    del report_schedules[schedule_id]
    
    logger.info(
        "REPORT_SCHEDULE_DELETED",
        schedule_id=schedule_id,
        user_id=getattr(request.state, "user_id", "unknown")
    )
    
    return {"message": "Report schedule deleted successfully"}


@router.post("/run-now/{schedule_id}")
async def run_report_now(
    request: Request,
    schedule_id: str,
    background_tasks: BackgroundTasks,
    run_request: Optional[ReportRunRequest] = None,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, str]:
    """Run a report schedule immediately."""
    if schedule_id not in report_schedules:
        raise HTTPException(status_code=404, detail="Report schedule not found")
    
    schedule = report_schedules[schedule_id]
    
    # Use provided recipients/filters or fall back to schedule defaults
    recipients = run_request.recipients if run_request and run_request.recipients else schedule.recipients
    filters = run_request.filters if run_request and run_request.filters else schedule.filters
    
    # Schedule background task to send report
    background_tasks.add_task(
        send_report,
        schedule_id,
        recipients,
        filters,
        manual=True
    )
    
    logger.info(
        "REPORT_RUN_NOW",
        schedule_id=schedule_id,
        recipients=recipients,
        manual=True,
        user_id=getattr(request.state, "user_id", "unknown")
    )
    
    return {"message": "Report queued for immediate sending"}


async def send_report(
    schedule_id: str,
    recipients: List[str],
    filters: Dict[str, Any],
    manual: bool = False
) -> None:
    """Send a report via email and/or Slack."""
    start_time = datetime.utcnow()
    
    try:
        # Fetch KPI data
        kpi_data = await fetch_kpi_data(filters)
        
        # Generate report content
        report_content = await generate_report_content(kpi_data, filters)
        
        # Send via configured channels
        schedule = report_schedules[schedule_id]
        
        if schedule.channel in [ReportChannel.email, ReportChannel.both]:
            await send_email_report(recipients, report_content, schedule.name)
        
        if schedule.channel in [ReportChannel.slack, ReportChannel.both]:
            await send_slack_report(recipients, report_content, schedule.name)
        
        # Update schedule statistics
        schedule.last_sent = datetime.utcnow()
        schedule.total_sent += 1
        schedule.next_send = calculate_next_send(schedule.frequency, schedule.time_hour, schedule.time_minute)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(
            "REPORT_SENT",
            schedule_id=schedule_id,
            recipients=recipients,
            processing_time_ms=processing_time,
            manual=manual
        )
        
    except Exception as e:
        # Update failure statistics
        if schedule_id in report_schedules:
            report_schedules[schedule_id].total_failed += 1
        
        processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.error(
            "REPORT_SEND_FAILED",
            schedule_id=schedule_id,
            recipients=recipients,
            error=str(e),
            processing_time_ms=processing_time,
            manual=manual
        )


async def fetch_kpi_data(filters: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch KPI data based on filters."""
    # This would integrate with the task service to get actual KPI data
    # For now, return mock data
    return {
        "summary": {
            "total_items": 1250,
            "manual_percentage": 23.5,
            "avg_time_per_task": 4.2,
            "total_tasks": 45,
            "completed_tasks": 42
        },
        "daily_stats": [
            {"date": "2024-01-15", "value": 150, "type": "total_items"},
            {"date": "2024-01-14", "value": 145, "type": "total_items"},
            {"date": "2024-01-13", "value": 160, "type": "total_items"}
        ],
        "top_workers": [
            {"worker_name": "Marko Šef", "completed_tasks": 25},
            {"worker_name": "Ana Radnik", "completed_tasks": 20},
            {"worker_name": "Petar Worker", "completed_tasks": 18}
        ],
        "manual_completion": [
            {"type": "scanned", "value": 850},
            {"type": "manual", "value": 200}
        ]
    }


async def generate_report_content(kpi_data: Dict[str, Any], filters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate report content including charts and CSV data."""
    return {
        "summary": kpi_data["summary"],
        "charts": {
            "daily_trend": kpi_data["daily_stats"],
            "top_workers": kpi_data["top_workers"],
            "manual_completion": kpi_data["manual_completion"]
        },
        "csv_data": generate_csv_data(kpi_data),
        "filters": filters,
        "generated_at": datetime.utcnow().isoformat()
    }


def generate_csv_data(kpi_data: Dict[str, Any]) -> str:
    """Generate CSV data in Pantheon MP format."""
    summary = kpi_data["summary"]
    top_workers = kpi_data["top_workers"]
    
    csv_lines = [
        "Broj dokumenta;Radnja;Odgovorna osoba;Datum",
        f"RPT-{datetime.now().strftime('%Y%m%d')};Magacin;Sistem;{datetime.now().strftime('%d.%m.%Y')}",
        "",
        "Šifra;Naziv;Količina;Cijena;Ukupno"
    ]
    
    # Add worker performance data
    for i, worker in enumerate(top_workers[:5], 1):
        csv_lines.append(f"WRK-{i:03d};{worker['worker_name']};{worker['completed_tasks']};1.00;{worker['completed_tasks']}.00")
    
    csv_lines.extend([
        "",
        f"UKUPNO;;;{summary['total_tasks']}.00",
        "",
        "Potpis odgovorne osobe;________________",
        f"Datum potvrde;{datetime.now().strftime('%d.%m.%Y')}"
    ])
    
    return "\n".join(csv_lines)


async def send_email_report(recipients: List[str], report_content: Dict[str, Any], report_name: str) -> None:
    """Send report via email."""
    from ..services.email_service import send_email_report as send_email
    await send_email(recipients, report_content, report_name)


async def send_slack_report(recipients: List[str], report_content: Dict[str, Any], report_name: str) -> None:
    """Send report via Slack webhook."""
    from ..services.slack_service import send_slack_report as send_slack
    await send_slack(recipients, report_content, report_name)


@router.get("/schedules/{schedule_id}/history")
async def get_report_history(
    schedule_id: str,
    limit: int = 10,
    _: None = Depends(require_roles(["SEF", "MENADZER"])),
) -> Dict[str, Any]:
    """Get report sending history for a schedule."""
    if schedule_id not in report_schedules:
        raise HTTPException(status_code=404, detail="Report schedule not found")
    
    # In production, this would query a database
    # For now, return mock history
    return {
        "schedule_id": schedule_id,
        "history": [
            {
                "sent_at": datetime.utcnow() - timedelta(hours=24),
                "recipients": ["admin@magacin.com"],
                "status": "success",
                "processing_time_ms": 1250
            },
            {
                "sent_at": datetime.utcnow() - timedelta(hours=48),
                "recipients": ["admin@magacin.com"],
                "status": "success",
                "processing_time_ms": 1100
            }
        ],
        "total": 2
    }
