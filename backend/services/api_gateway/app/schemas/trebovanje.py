from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class TrebovanjeItem(BaseModel):
    id: str
    artikl_sifra: str
    naziv: str
    kolicina_trazena: float
    kolicina_obradjena: float
    status: Literal["new", "assigned", "in_progress", "done"] = "new"


class Trebovanje(BaseModel):
    id: str
    dokument_broj: str
    datum: datetime
    magacin_naziv: str
    radnja_naziv: str
    status: Literal["new", "assigned", "in_progress", "done", "failed"] = "new"
    broj_stavki: int
    stavke: Optional[List[TrebovanjeItem]] = None


class TrebovanjeAssignRequest(BaseModel):
    magacioner_id: str
    stavka_ids: List[str]
    prioritet: Literal["low", "normal", "high"] = "normal"
    rok_iso: Optional[datetime] = None
