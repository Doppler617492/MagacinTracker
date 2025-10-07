from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CatalogBarcode(BaseModel):
    value: str
    is_primary: bool | None = None


class CatalogUpsertItem(BaseModel):
    sifra: str
    naziv: Optional[str] = None
    jedinica_mjere: Optional[str] = None
    barkodovi: List[CatalogBarcode] = Field(default_factory=list)
    aktivan: bool = True


class CatalogUpsertOptions(BaseModel):
    deactivate_missing: bool = False
    source: Optional[str] = None
    payload_hash: Optional[str] = None


class CatalogUpsertRequest(BaseModel):
    items: List[CatalogUpsertItem]
    options: CatalogUpsertOptions = CatalogUpsertOptions()


class CatalogUpsertResponse(BaseModel):
    processed: int
    created: int
    updated: int
    deactivated: int
    duration_ms: float
    cached: bool = False


class CatalogLookupResponse(BaseModel):
    artikal_id: UUID | None
    sifra: str
    naziv: Optional[str]
    jedinica_mjere: Optional[str]
    aktivan: bool
    barkodovi: List[CatalogBarcode]


class CatalogArticleResponse(BaseModel):
    id: UUID
    sifra: str
    naziv: str
    jedinica_mjere: str
    aktivan: bool
    barkodovi: List[CatalogBarcode]

    @staticmethod
    def from_model(artikal) -> "CatalogArticleResponse":
        return CatalogArticleResponse(
            id=artikal.id,
            sifra=artikal.sifra,
            naziv=artikal.naziv,
            jedinica_mjere=artikal.jedinica_mjere,
            aktivan=artikal.aktivan,
            barkodovi=[
                CatalogBarcode(value=b.barkod, is_primary=b.is_primary)
                for b in artikal.barkodovi
            ],
        )


class CatalogArticleUpdate(BaseModel):
    naziv: Optional[str] = None
    jedinica_mjere: Optional[str] = None
    aktivan: Optional[bool] = None
    barkodovi: Optional[List[CatalogBarcode]] = None


class CatalogArticleListResponse(BaseModel):
    items: List[CatalogArticleResponse]
    total: int
    page: int
    page_size: int
