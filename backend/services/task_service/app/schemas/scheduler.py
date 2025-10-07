from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SchedulerSuggestionRequest(BaseModel):
    trebovanje_id: UUID


class SchedulerSuggestionResponse(BaseModel):
    log_id: UUID
    trebovanje_id: UUID
    magacioner_id: UUID
    score: float
    reason: str
    lock_expires_at: datetime | None = None
    cached: bool = False
