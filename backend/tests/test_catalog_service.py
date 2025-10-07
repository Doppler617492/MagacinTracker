import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest

from services.catalog_service.app.config import settings
from services.catalog_service.app.schemas import CatalogSyncSummary, CatalogSyncTriggerRequest
from services.catalog_service.app.services.sync import CatalogSyncRunner


class DummyResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self) -> dict[str, Any]:
        return self._payload


class DummyAsyncClient:
    def __init__(self, responses: list[DummyResponse], recorder: list[dict[str, Any]], *args, **kwargs) -> None:
        self._responses = responses
        self._recorder = recorder

    async def __aenter__(self) -> "DummyAsyncClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def post(self, url: str, json: dict[str, Any], headers: dict[str, str]) -> DummyResponse:
        self._recorder.append({"url": url, "json": json, "headers": headers})
        if not self._responses:
            raise AssertionError("No more dummy responses configured")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_catalog_runner_builds_payload_and_posts(monkeypatch, tmp_path: Path) -> None:
    catalog_data = [
        {
            "sifra": "A-1",
            "naziv": "Artikal 1",
            "jm": "kom",
            "barkodovi": [{"value": "123"}],
        },
        {
            "sifra": "A-2",
            "naziv": "Artikal 2",
            "aktivan": False,
        },
    ]
    catalog_file = tmp_path / "catalog.json"
    catalog_file.write_text(json.dumps(catalog_data), encoding="utf-8")

    monkeypatch.setattr(settings, "catalog_sync_source", "FILE", raising=False)
    monkeypatch.setattr(settings, "catalog_sync_path", catalog_file, raising=False)
    monkeypatch.setattr(settings, "catalog_sync_deactivate_missing", True, raising=False)

    recorded_requests: list[dict[str, Any]] = []
    responses = [
        DummyResponse(
            200,
            {
                "processed": 2,
                "created": 2,
                "updated": 0,
                "deactivated": 0,
                "duration_ms": 12.5,
                "cached": False,
            },
        )
    ]

    def _client_factory(*args, **kwargs):
        return DummyAsyncClient(responses, recorded_requests, *args, **kwargs)

    monkeypatch.setattr("services.catalog_service.app.services.sync.httpx.AsyncClient", _client_factory)

    runner = CatalogSyncRunner()
    summary = await runner.trigger(initiated_by=uuid4())

    assert isinstance(summary, CatalogSyncSummary)
    assert summary.status == "success"
    assert summary.processed == 2
    assert summary.cached is False
    assert recorded_requests, "Expected request to Task service"

    request_payload = recorded_requests[0]["json"]
    assert request_payload["options"]["deactivate_missing"] is True
    assert request_payload["options"]["source"] == "FILE"
    assert request_payload["options"].get("payload_hash")
    first_hash = request_payload["options"]["payload_hash"]

    # second run with same data should reuse identical hash and mark cached when Task responds 202
    recorded_requests.clear()
    responses.extend(
        [
            DummyResponse(
                202,
                {
                    "processed": 2,
                    "created": 0,
                    "updated": 0,
                    "deactivated": 0,
                    "duration_ms": 9.1,
                    "cached": True,
                },
            )
        ]
    )

    summary_cached = await runner.trigger(initiated_by=uuid4())
    assert summary_cached.status == "cached"
    assert summary_cached.cached is True
    assert recorded_requests, "Expected second request"
    second_payload = recorded_requests[0]["json"]
    assert second_payload["options"]["payload_hash"] == first_hash

    auth_header = recorded_requests[0]["headers"].get("Authorization")
    assert auth_header == f"Bearer {settings.service_token}"


@pytest.mark.asyncio
async def test_catalog_runner_raises_for_missing_source(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(settings, "catalog_sync_source", "FILE", raising=False)
    monkeypatch.setattr(settings, "catalog_sync_path", tmp_path / "missing.json", raising=False)

    runner = CatalogSyncRunner()
    with pytest.raises(FileNotFoundError):
        await runner.trigger(initiated_by=None, trigger=CatalogSyncTriggerRequest())
