from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class KPISummaryResponse(BaseModel):
    period_days: int
    start_date: str
    end_date: str
    filters: Dict[str, Optional[str]]
    summary: Dict[str, Any]


class DailyStatsResponse(BaseModel):
    date: str
    trebovanja_count: int
    stavke_count: float


class TopWorkerResponse(BaseModel):
    radnik_id: str
    ime: str
    prezime: str
    total_zadaci: int
    completed_zadaci: int
    completion_rate: float


class ManualCompletionStatsResponse(BaseModel):
    total_scans: int
    manual_scans: int
    manual_percentage: float
    scan_percentage: float


class KPIFilters(BaseModel):
    radnja_id: Optional[uuid.UUID] = Field(None, description="Filter by radnja ID")
    radnik_id: Optional[uuid.UUID] = Field(None, description="Filter by radnik ID")
    days: int = Field(7, ge=1, le=365, description="Number of days to analyze")


class CSVExportRequest(BaseModel):
    radnja_id: Optional[uuid.UUID] = Field(None, description="Filter by radnja ID")
    radnik_id: Optional[uuid.UUID] = Field(None, description="Filter by radnik ID")
    start_date: datetime = Field(..., description="Start date for export")
    end_date: datetime = Field(..., description="End date for export")
    include_details: bool = Field(False, description="Include detailed breakdown")


class CSVExportResponse(BaseModel):
    filename: str
    download_url: str
    record_count: int
    generated_at: datetime
