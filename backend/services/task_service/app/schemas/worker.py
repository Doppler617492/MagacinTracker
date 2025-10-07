from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from ..models.enums import ZaduznicaStatus


class WorkerTaskItem(BaseModel):
    id: UUID
    naziv: str
    trazena_kolicina: float
    obradjena_kolicina: float
    status: str
    needs_barcode: bool

    model_config = {"from_attributes": True}


class WorkerTask(BaseModel):
    id: UUID
    dokument: str
    lokacija: str
    stavke_total: int
    progress: float
    status: ZaduznicaStatus
    due_at: datetime | None


class WorkerTaskDetail(WorkerTask):
    stavke: List[WorkerTaskItem]
