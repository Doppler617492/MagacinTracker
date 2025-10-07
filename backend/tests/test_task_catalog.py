import uuid

import pytest
from sqlalchemy import select

from services.task_service.app.models import Artikal, ArtikalBarkod, AuditLog, CatalogSyncStatus
from services.task_service.app.models.enums import AuditAction
from services.task_service.app.schemas import (
    CatalogBarcode,
    CatalogUpsertItem,
    CatalogUpsertOptions,
    CatalogUpsertRequest,
)
from services.task_service.app.services.catalog import CatalogService


@pytest.mark.asyncio
async def test_catalog_upsert_create_update_deactivate(async_session):
    service = CatalogService(async_session)
    actor_id = uuid.uuid4()

    initial_request = CatalogUpsertRequest(
        items=[
            CatalogUpsertItem(
                sifra="A-001",
                naziv="Artikal 1",
                jedinica_mjere="kom",
                aktivan=True,
                barkodovi=[
                    CatalogBarcode(value="1111111111111", is_primary=True),
                    CatalogBarcode(value="1111111111112", is_primary=False),
                ],
            ),
            CatalogUpsertItem(
                sifra="A-002",
                naziv="Artikal 2",
                jedinica_mjere="pak",
                aktivan=True,
                barkodovi=[CatalogBarcode(value="2222222222222", is_primary=True)],
            ),
        ],
        options=CatalogUpsertOptions(source="test", payload_hash="batch-1"),
    )

    first_response, cached = await service.upsert_batch(initial_request, executed_by=actor_id)
    assert not cached
    assert first_response.created == 2
    assert first_response.updated == 0
    assert first_response.deactivated == 0

    artikli = (await async_session.execute(select(Artikal))).scalars().all()
    assert len(artikli) == 2
    assert all(a.aktivan for a in artikli)

    # prepare update request that should deactivate missing and flip primary barcode
    update_request = CatalogUpsertRequest(
        items=[
            CatalogUpsertItem(
                sifra="A-001",
                naziv="Artikal 1 updated",
                jedinica_mjere="pak",
                aktivan=True,
                barkodovi=[
                    CatalogBarcode(value="1111111111112", is_primary=True),
                    CatalogBarcode(value="1111111111111", is_primary=False),
                ],
            )
        ],
        options=CatalogUpsertOptions(
            source="test",
            deactivate_missing=True,
            payload_hash="batch-2",
        ),
    )

    second_response, cached = await service.upsert_batch(update_request, executed_by=actor_id)
    assert not cached
    assert second_response.created == 0
    assert second_response.updated == 1
    assert second_response.deactivated == 1

    artikal_one = await async_session.scalar(select(Artikal).where(Artikal.sifra == "A-001"))
    artikal_two = await async_session.scalar(select(Artikal).where(Artikal.sifra == "A-002"))
    assert artikal_one is not None
    assert artikal_one.naziv == "Artikal 1 updated"
    assert artikal_one.jedinica_mjere == "pak"
    assert artikal_two is not None
    assert artikal_two.aktivan is False

    barcodes = (
        await async_session.execute(
            select(ArtikalBarkod).where(ArtikalBarkod.artikal_id == artikal_one.id)
        )
    ).scalars().all()
    assert len(barcodes) == 2
    primary_flags = [barcode.is_primary for barcode in barcodes]
    assert primary_flags.count(True) == 1
    assert any(barcode.barkod == "1111111111112" and barcode.is_primary for barcode in barcodes)

    # third call with identical payload_hash should be treated as cached
    cached_response, cached = await service.upsert_batch(update_request, executed_by=actor_id)
    assert cached
    assert cached_response.cached is True

    sync_entries = (await async_session.execute(select(CatalogSyncStatus))).scalars().all()
    assert len(sync_entries) == 2  # first two successful runs only

    audit_entries = (
        await async_session.execute(select(AuditLog).where(AuditLog.action == AuditAction.catalog_sync))
    ).scalars().all()
    assert len(audit_entries) == 2
