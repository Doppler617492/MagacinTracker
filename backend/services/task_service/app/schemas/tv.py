from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel


class LeaderboardEntry(BaseModel):
    user_id: str
    display_name: str
    items_completed: int
    task_completion: float
    speed_per_hour: float


class QueueEntry(BaseModel):
    dokument: str
    radnja: str
    status: str
    assigned_to: List[str]
    eta_minutes: float | None = None


class KpiSnapshot(BaseModel):
    total_tasks_today: int
    completed_percentage: float
    active_workers: int
    shift_ends_in_minutes: float


class TvSnapshot(BaseModel):
    generated_at: datetime
    leaderboard: List[LeaderboardEntry]
    queue: List[QueueEntry]
    kpi: KpiSnapshot
