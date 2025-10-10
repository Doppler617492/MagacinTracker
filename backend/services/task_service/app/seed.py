from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import select

from app_common.db import SessionLocal
from app_common.security import get_password_hash

from .models import Magacin, Radnja, UserAccount, UserRole
from .models.enums import Role

DEFAULT_PASSWORD = "Magacin123!"

USERS = [
    {
        "id": uuid.UUID("00000000-0000-0000-0000-000000000001"),
        "email": "import.service@example.com",
        "full_name": "Import Service",
        "roles": [Role.KOMERCIJALISTA],
    },
    {
        "id": uuid.UUID("11111111-1111-1111-1111-111111111111"),
        "email": "ana.komercijalista@example.com",
        "full_name": "Ana Komercijalista",
        "roles": [Role.KOMERCIJALISTA],
    },
    {
        "id": uuid.UUID("22222222-2222-2222-2222-222222222222"),
        "email": "marko.sef@example.com",
        "full_name": "Marko Šef",
        "roles": [Role.SEF],
    },
    {
        "id": uuid.UUID("33333333-3333-3333-3333-333333333333"),
        "email": "luka.magacioner@example.com",
        "full_name": "Luka Magacioner",
        "roles": [Role.MAGACIONER],
    },
    {
        "id": uuid.UUID("44444444-4444-4444-4444-444444444444"),
        "email": "milos.magacioner@example.com",
        "full_name": "Miloš Magacioner",
        "roles": [Role.MAGACIONER],
    },
    {
        "id": uuid.UUID("55555555-5555-5555-5555-555555555555"),
        "email": "jelena.magacioner@example.com",
        "full_name": "Jelena Magacioner",
        "roles": [Role.MAGACIONER],
    },
    {
        "id": uuid.UUID("66666666-6666-6666-6666-666666666666"),
        "email": "vanja.menadzer@example.com",
        "full_name": "Vanja Menadžer",
        "roles": [Role.MENADZER],
    },
]

WAREHOUSES = [
    {
        "id": uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        "pantheon_id": "veleprodajni_magacin",
        "naziv": "Veleprodajni Magacin",
    },
]

STORES = [
    {
        "id": uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
        "pantheon_id": "prodavnica_podgorica",
        "naziv": "Prodavnica Podgorica",
    },
    {
        "id": uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc"),
        "pantheon_id": "prodavnica_niksic",
        "naziv": "Prodavnica Nikšić",
    },
    {
        "id": uuid.UUID("dddddddd-dddd-dddd-dddd-dddddddddddd"),
        "pantheon_id": "prodavnica_kotor_centar",
        "naziv": "Prodavnica - Kotor Centar",
    },
]


async def seed_users() -> None:
    async with SessionLocal() as session:
        for record in USERS:
            existing = await session.scalar(select(UserAccount).where(UserAccount.email == record["email"]))
            if existing:
                continue

            user = UserAccount(
                id=record["id"],
                email=record["email"],
                full_name=record["full_name"],
                password_hash=get_password_hash(DEFAULT_PASSWORD),
            )
            session.add(user)
            await session.flush()

            for role in record["roles"]:
                session.add(UserRole(id=uuid.uuid4(), user_id=user.id, role=role))

        await session.commit()


async def seed_locations() -> None:
    async with SessionLocal() as session:
        for magacin in WAREHOUSES:
            exists = await session.scalar(
                select(Magacin).where(Magacin.pantheon_id == magacin["pantheon_id"])  # type: ignore[arg-type]
            )
            if not exists:
                session.add(
                    Magacin(id=magacin["id"], pantheon_id=magacin["pantheon_id"], naziv=magacin["naziv"])
                )

        for store in STORES:
            exists = await session.scalar(
                select(Radnja).where(Radnja.pantheon_id == store["pantheon_id"])  # type: ignore[arg-type]
            )
            if not exists:
                session.add(
                    Radnja(id=store["id"], pantheon_id=store["pantheon_id"], naziv=store["naziv"])
                )

        await session.commit()


async def main() -> None:
    await seed_users()
    await seed_locations()
    print("Seed data inserted (users, roles, magacin, radnje)")


if __name__ == "__main__":
    asyncio.run(main())
