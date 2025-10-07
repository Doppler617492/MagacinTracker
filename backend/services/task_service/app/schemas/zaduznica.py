from __future__ import annotations

from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import TaskPriority, ZaduznicaItemStatus, ZaduznicaStatus


class TrebovanjeAssignItem(BaseModel):
    trebovanje_stavka_id: UUID
    quantity: float = Field(gt=0)


class ZaduznicaAssignment(BaseModel):
    magacioner_id: UUID
    priority: TaskPriority = TaskPriority.normal
    due_at: datetime | None = None
    items: List[TrebovanjeAssignItem]


class ZaduznicaCreateRequest(BaseModel):
    trebovanje_id: UUID
    assignments: List[ZaduznicaAssignment]


class ZaduznicaCreateResponse(BaseModel):
    zaduznica_ids: List[UUID]


class ZaduznicaStatusUpdate(BaseModel):
    status: ZaduznicaStatus


class ZaduznicaReassignRequest(BaseModel):
    target_magacioner_id: UUID


class ScanRequest(BaseModel):
    barcode: str
    quantity: float = Field(default=1, gt=0)


class ManualCompleteRequest(BaseModel):
    quantity: float = Field(gt=0)
    reason: str = Field(min_length=3, max_length=255)


class ZaduznicaItemDetail(BaseModel):
    id: UUID
    trebovanje_stavka_id: UUID
    naziv: str
    trazena_kolicina: float
    obradjena_kolicina: float
    status: ZaduznicaItemStatus

    model_config = {"from_attributes": True}


class ZaduznicaDetail(BaseModel):
    id: UUID
    dokument: str
    lokacija: str
    radnja: str
    status: ZaduznicaStatus
    prioritet: TaskPriority
    due_at: datetime | None
    progress: float
    stavke: List[ZaduznicaItemDetail]

    model_config = {"from_attributes": True}
