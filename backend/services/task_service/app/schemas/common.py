from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class PaginationQuery(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = None
    magacin_id: Optional[str] = None
    radnja_id: Optional[str] = None
    search: Optional[str] = None
