from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import List, Optional

from pydantic import AliasChoices, BaseModel, Field


class CatalogBarcode(BaseModel):
    value: str
    is_primary: bool | None = None


class CatalogItem(BaseModel):
    sifra: str
    naziv: Optional[str] = None
    jedinica_mjere: Optional[str] = Field(
        default=None,
        alias="jedinica_mjere",
        validation_alias=AliasChoices("jedinica_mjere", "jm"),
    )
    barkodovi: List[CatalogBarcode] = Field(default_factory=list)
    aktivan: bool = True

    def to_task_payload(self) -> dict:
        return {
            "sifra": self.sifra,
            "naziv": self.naziv,
            "jedinica_mjere": self.jedinica_mjere,
            "barkodovi": [barcode.model_dump(exclude_none=True) for barcode in self.barkodovi],
            "aktivan": self.aktivan,
        }


class CatalogSyncOptions(BaseModel):
    deactivate_missing: bool = False
    source: Optional[str] = None
    payload_hash: Optional[str] = None


class CatalogUpsertBatch(BaseModel):
    items: List[CatalogItem]
    options: CatalogSyncOptions = CatalogSyncOptions()

    def to_task_payload(self) -> dict:
        payload = {
            "items": [item.to_task_payload() for item in self.items],
            "options": self.options.model_dump(exclude_none=True),
        }
        if not payload["options"].get("payload_hash"):
            payload_hash = hashlib.sha256(
                json.dumps(payload["items"], sort_keys=True, separators=(",", ":")).encode("utf-8")
            ).hexdigest()
            payload["options"]["payload_hash"] = payload_hash
        return payload


class CatalogSyncTriggerRequest(BaseModel):
    source: Optional[str] = None
    deactivate_missing: Optional[bool] = None
    path: Optional[str] = None


class CatalogSyncSummary(BaseModel):
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    processed: Optional[int] = None
    created: Optional[int] = None
    updated: Optional[int] = None
    deactivated: Optional[int] = None
    cached: bool = False
    source: Optional[str] = None
    payload_hash: Optional[str] = None
    message: Optional[str] = None


class CatalogStatusResponse(BaseModel):
    last_run: Optional[CatalogSyncSummary] = None
