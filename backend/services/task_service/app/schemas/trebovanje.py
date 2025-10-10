from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.enums import TrebovanjeStatus


class TrebovanjeListItem(BaseModel):
    id: UUID
    dokument_broj: str
    datum: datetime
    magacin: str
    radnja: str
    status: TrebovanjeStatus
    broj_stavki: int
    ukupno_trazena: float
    ukupno_uradjena: float

    model_config = {"from_attributes": True}


class TrebovanjeItemDetail(BaseModel):
    id: UUID
    artikl_sifra: str
    naziv: str
    kolicina_trazena: float
    kolicina_uradjena: float
    status: str
    needs_barcode: bool | None = None

    model_config = {"from_attributes": True}


class TrebovanjeDetail(BaseModel):
    id: UUID
    dokument_broj: str
    datum: datetime
    status: TrebovanjeStatus
    magacin: str
    radnja: str
    broj_stavki: int
    stavke: List[TrebovanjeItemDetail]

    model_config = {"from_attributes": True}


class TrebovanjeListResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[TrebovanjeListItem]


class TrebovanjeStavkaInput(BaseModel):
    artikl_id: Optional[UUID] = None
    artikl_sifra: str
    naziv: str
    kolicina_trazena: float = Field(gt=0)
    barkod: Optional[str] = None
    needs_barcode: bool = False


class TrebovanjeImportPayload(BaseModel):
    dokument_broj: str
    datum: datetime
    magacin_pantheon_id: str
    magacin_naziv: Optional[str] = None
    radnja_pantheon_id: str
    radnja_naziv: Optional[str] = None
    meta: dict = Field(default_factory=dict)
    stavke: List[TrebovanjeStavkaInput]
