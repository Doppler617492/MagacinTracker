from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from ..models.enums import DiscrepancyStatus, ZaduznicaStatus


class WorkerTaskItem(BaseModel):
    id: UUID
    naziv: str
    artikl_sifra: str
    kolicina_trazena: float
    picked_qty: float
    missing_qty: float
    discrepancy_status: str
    discrepancy_reason: Optional[str] = None
    needs_barcode: bool
    barkod: Optional[str] = None

    model_config = {"from_attributes": True}


class WorkerTask(BaseModel):
    id: UUID
    dokument: str
    dokument_broj: str  # Added for PWA compatibility
    lokacija: str
    lokacija_naziv: str  # Added for PWA compatibility  
    stavke_total: int
    stavke_completed: int  # Added for PWA compatibility
    partial_items: int = 0
    shortage_qty: float = 0
    assigned_by_id: UUID | None = None
    assigned_by_name: str | None = None
    progress: float
    status: ZaduznicaStatus
    due_at: datetime | None
    trebovanje_id: UUID  # Added for document completion


class WorkerTaskDetail(WorkerTask):
    stavke: List[WorkerTaskItem]
