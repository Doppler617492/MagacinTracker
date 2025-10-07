from typing import Any

import pytest

from services.import_service.app.services.processor import ImportProcessor


class DummyResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

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

    async def get(self, url: str, params: dict | None = None, headers: dict | None = None) -> DummyResponse:
        self._recorder.append({"url": url, "params": params, "headers": headers})
        if not self._responses:
            raise AssertionError("No more dummy responses available")
        return self._responses.pop(0)


@pytest.mark.asyncio
async def test_enrich_payload_uses_catalog_lookup(monkeypatch) -> None:
    responses = [
        DummyResponse(
            {
                "artikal_id": "11111111-1111-1111-1111-111111111111",
                "barkodovi": [
                    {"value": "1234567890123", "is_primary": True},
                    {"value": "9876543210987", "is_primary": False},
                ],
            }
        ),
        DummyResponse(
            {
                "artikal_id": None,
                "barkodovi": [],
            }
        ),
    ]
    recorded: list[dict[str, Any]] = []

    def _client_factory(*args, **kwargs):
        return DummyAsyncClient(responses, recorded, *args, **kwargs)

    monkeypatch.setattr(
        "services.import_service.app.services.processor.httpx.AsyncClient",
        _client_factory,
    )

    processor = ImportProcessor()
    payload = {
        "stavke": [
            {"artikl_sifra": "A-1", "naziv": "Prvi", "barkod": None},
            {"artikl_sifra": "A-2", "naziv": "Drugi"},
        ]
    }

    await processor._enrich_payload(payload)

    assert payload["stavke"][0]["artikl_id"] == "11111111-1111-1111-1111-111111111111"
    assert payload["stavke"][0]["barkod"] == "1234567890123"
    assert payload["stavke"][0]["needs_barcode"] is False

    assert "artikl_id" not in payload["stavke"][1]
    assert payload["stavke"][1].get("barkod") is None
    assert payload["stavke"][1]["needs_barcode"] is True

    assert recorded, "Expected lookup requests"
    first_request = recorded[0]
    assert first_request["params"] == {"sifra": "A-1"}
    assert "Authorization" in first_request["headers"]
