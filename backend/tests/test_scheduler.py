import uuid
from datetime import datetime, timezone

import pytest

from services.task_service.app.models import (
    Artikal,
    Magacin,
    Radnja,
    SchedulerLog,
    Trebovanje,
    TrebovanjeStavka,
    UserAccount,
    UserRole,
    Zaduznica,
    ZaduznicaStavka,
)
from services.task_service.app.models.enums import Role, ZaduznicaItemStatus, ZaduznicaStatus
from services.task_service.app.services.scheduler import SchedulerLockManager, SchedulerService


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    async def get(self, key: str):
        return self.store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.store[key] = value

    async def delete(self, key: str):
        self.store.pop(key, None)


@pytest.mark.asyncio
async def test_scheduler_selects_least_loaded_worker(async_session, monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(
        "services.task_service.app.services.scheduler.get_redis",
        lambda: fake_redis,
    )

    sef_id = uuid.uuid4()
    sef = UserAccount(
        id=sef_id,
        email="sef@example.com",
        full_name="Sef",
        password_hash="hashed",
        is_active=True,
    )
    sef_role = UserRole(user_id=sef_id, role=Role.sef)

    mag1_id = uuid.uuid4()
    mag1 = UserAccount(
        id=mag1_id,
        email="mag1@example.com",
        full_name="Magacioner 1",
        password_hash="hashed",
        is_active=True,
    )
    mag1_role = UserRole(user_id=mag1_id, role=Role.magacioner)

    mag2_id = uuid.uuid4()
    mag2 = UserAccount(
        id=mag2_id,
        email="mag2@example.com",
        full_name="Magacioner 2",
        password_hash="hashed",
        is_active=True,
    )
    mag2_role = UserRole(user_id=mag2_id, role=Role.magacioner)

    magacin = Magacin(id=uuid.uuid4(), pantheon_id="magacin-1", naziv="Magacin 1")
    radnja = Radnja(id=uuid.uuid4(), pantheon_id="radnja-1", naziv="Radnja 1")

    trebovanje_id = uuid.uuid4()
    trebovanje = Trebovanje(
        id=trebovanje_id,
        dokument_broj="DOC-001",
        datum=datetime.now(timezone.utc),
        magacin_id=magacin.id,
        radnja_id=radnja.id,
    )

    artikal = Artikal(id=uuid.uuid4(), sifra="A-1", naziv="Artikal 1", jedinica_mjere="kom")
    stavka = TrebovanjeStavka(
        id=uuid.uuid4(),
        trebovanje_id=trebovanje_id,
        artikal_id=artikal.id,
        artikl_sifra="A-1",
        naziv="Artikal 1",
        kolicina_trazena=10,
        kolicina_uradjena=0,
    )

    zaduznica = Zaduznica(
        id=uuid.uuid4(),
        trebovanje_id=trebovanje_id,
        magacioner_id=mag1_id,
        status=ZaduznicaStatus.assigned,
    )
    zaduznica_stavka = ZaduznicaStavka(
        id=uuid.uuid4(),
        zaduznica_id=zaduznica.id,
        trebovanje_stavka_id=stavka.id,
        trazena_kolicina=10,
        obradjena_kolicina=2,
        status=ZaduznicaItemStatus.in_progress,
    )

    async_session.add_all([
        sef,
        sef_role,
        mag1,
        mag1_role,
        mag2,
        mag2_role,
        magacin,
        radnja,
        artikal,
        trebovanje,
        stavka,
        zaduznica,
        zaduznica_stavka,
    ])
    await async_session.commit()

    scheduler = SchedulerService(async_session)
    log_entry, cached = await scheduler.suggest(trebovanje_id, actor_id=sef_id)

    assert not cached
    assert log_entry.magacioner_id == mag2_id
    assert log_entry.score >= 0

    # second call returns cached suggestion
    log_entry_again, cached_again = await scheduler.suggest(trebovanje_id, actor_id=sef_id)
    assert cached_again
    assert log_entry_again.id == log_entry.id


@pytest.mark.asyncio
async def test_scheduler_no_workers(async_session, monkeypatch):
    fake_redis = FakeRedis()
    monkeypatch.setattr(
        "services.task_service.app.services.scheduler.get_redis",
        lambda: fake_redis,
    )

    magacin = Magacin(id=uuid.uuid4(), pantheon_id="magacin-1", naziv="Magacin 1")
    radnja = Radnja(id=uuid.uuid4(), pantheon_id="radnja-1", naziv="Radnja 1")
    trebovanje_id = uuid.uuid4()
    trebovanje = Trebovanje(
        id=trebovanje_id,
        dokument_broj="DOC-002",
        datum=datetime.now(timezone.utc),
        magacin_id=magacin.id,
        radnja_id=radnja.id,
    )
    async_session.add_all([magacin, radnja, trebovanje])
    await async_session.commit()

    scheduler = SchedulerService(async_session)
    with pytest.raises(ValueError):
        await scheduler.suggest(trebovanje_id, actor_id=None)
