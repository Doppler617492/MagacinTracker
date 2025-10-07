import uuid
from datetime import datetime, timezone

import pytest

from services.task_service.app.models import Magacin, Radnja, Trebovanje, TrebovanjeStavka, Zaduznica, ZaduznicaStavka
from services.task_service.app.models.enums import TaskPriority, TrebovanjeStatus, ZaduznicaItemStatus, ZaduznicaStatus
from services.task_service.app.schemas import ScanRequest
from services.task_service.app.services import zaduznice


@pytest.mark.asyncio
async def test_register_scan_promotes_status(async_session, monkeypatch):
    async def noop_publish(*args, **kwargs):
        return None

    monkeypatch.setattr(zaduznice, "publish", noop_publish)
    trebovanje_id = uuid.uuid4()
    stavka_id = uuid.uuid4()
    zaduznica_id = uuid.uuid4()

    magacin = Magacin(id=uuid.uuid4(), pantheon_id="test_magacin", naziv="Test Magacin")
    radnja = Radnja(id=uuid.uuid4(), pantheon_id="test_radnja", naziv="Test Radnja")
    trebovanje = Trebovanje(
        id=trebovanje_id,
        dokument_broj="DOC-1",
        datum=datetime.now(timezone.utc),
        magacin_id=magacin.id,
        radnja_id=radnja.id,
        status=TrebovanjeStatus.new,
    )
    stavka = TrebovanjeStavka(
        id=stavka_id,
        trebovanje_id=trebovanje_id,
        artikl_sifra="200431",
        naziv="Jastuk KING",
        kolicina_trazena=10,
    )
    zaduznica_obj = Zaduznica(
        id=zaduznica_id,
        trebovanje_id=trebovanje_id,
        magacioner_id=uuid.uuid4(),
        prioritet=TaskPriority.normal,
        status=ZaduznicaStatus.assigned,
    )
    zaduznica_stavka = ZaduznicaStavka(
        id=uuid.uuid4(),
        zaduznica_id=zaduznica_id,
        trebovanje_stavka_id=stavka_id,
        trazena_kolicina=10,
    )

    async_session.add_all([magacin, radnja, trebovanje, stavka, zaduznica_obj, zaduznica_stavka])
    await async_session.commit()

    await zaduznice.register_scan(
        async_session,
        zaduznica_stavka.id,
        payload=ScanRequest(barcode="123", quantity=10),
        actor_id=uuid.uuid4(),
    )

    await async_session.refresh(zaduznica_stavka)
    await async_session.refresh(zaduznica_obj)
    await async_session.refresh(stavka)
    await async_session.refresh(trebovanje)

    assert zaduznica_stavka.status == ZaduznicaItemStatus.done
    assert stavka.status == zaduznica_stavka.status
    assert zaduznica_obj.status == ZaduznicaStatus.done
    assert trebovanje.status == TrebovanjeStatus.done
