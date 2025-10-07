import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from services.task_service.app.models import Trebovanje, TrebovanjeStavka, Zaduznica, ZaduznicaStavka
from services.task_service.app.models.enums import TrebovanjeItemStatus, TrebovanjeStatus, ZaduznicaItemStatus, ZaduznicaStatus
from services.task_service.app.repositories.trebovanje import TrebovanjeRepository
from services.task_service.app.schemas import (
    ScanRequest,
    TrebovanjeImportPayload,
    ZaduznicaAssignment,
    ZaduznicaCreateRequest,
)
from services.task_service.app.services import zaduznice


@pytest.mark.asyncio
async def test_happy_flow_import_assign_scan(async_session, monkeypatch):
    async def noop_publish(*args, **kwargs):
        return None

    monkeypatch.setattr(zaduznice, "publish", noop_publish)
    repo = TrebovanjeRepository(async_session)

    payload = TrebovanjeImportPayload(
        dokument_broj="DOC-2025",
        datum=datetime.now(timezone.utc),
        magacin_pantheon_id="veleprodajni_magacin",
        magacin_naziv="Veleprodajni Magacin",
        radnja_pantheon_id="prodavnica_kotor_centar",
        radnja_naziv="Prodavnica - Kotor Centar",
        stavke=[
          {
            "artikl_sifra": "200431",
            "naziv": "Jastuk KING",
            "kolicina_trazena": 5,
            "barkod": "8600100200431"
          }
        ],
    )

    detail = await repo.create_from_import(payload, initiated_by=uuid.uuid4())
    assert detail.status == TrebovanjeStatus.new

    assignment = ZaduznicaAssignment(
        magacioner_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
        priority="normal",
        due_at=None,
        items=[{"trebovanje_stavka_id": uuid.UUID(str(detail.stavke[0].id)), "quantity": 5}],
    )
    request = ZaduznicaCreateRequest(trebovanje_id=uuid.UUID(str(detail.id)), assignments=[assignment])
    created_ids = await zaduznice.create_zaduznice(async_session, request, actor_id=uuid.uuid4())

    assert created_ids, "Expected zadužnica IDs"

    zaduznica_stavka = await async_session.scalar(
        select(ZaduznicaStavka).where(ZaduznicaStavka.zaduznica_id == created_ids[0])
    )
    assert zaduznica_stavka is not None

    await zaduznice.register_scan(
        async_session,
        zaduznica_stavka.id,
        payload=ScanRequest(barcode="8600100200431", quantity=5),
        actor_id=uuid.UUID("33333333-3333-3333-3333-333333333333"),
    )

    await async_session.refresh(zaduznica_stavka)
    trebovanje_stavka = await async_session.get(TrebovanjeStavka, zaduznica_stavka.trebovanje_stavka_id)
    zaduznica = await async_session.get(Zaduznica, created_ids[0])
    trebovanje = await async_session.get(Trebovanje, uuid.UUID(str(detail.id)))

    assert zaduznica_stavka.status == ZaduznicaItemStatus.done
    assert trebovanje_stavka and trebovanje_stavka.status == TrebovanjeItemStatus.done
    assert zaduznica and zaduznica.status == ZaduznicaStatus.done
    assert trebovanje and trebovanje.status == TrebovanjeStatus.done
