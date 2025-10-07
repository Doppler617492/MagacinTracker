from __future__ import annotations

import asyncio
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import httpx
from prometheus_client import Counter, Histogram

from app_common.logging import get_logger

from ..config import settings
from ..schemas import (
    CatalogItem,
    CatalogStatusResponse,
    CatalogSyncOptions,
    CatalogSyncSummary,
    CatalogSyncTriggerRequest,
    CatalogUpsertBatch,
)

logger = get_logger(__name__)

CATALOG_SYNC_DURATION = Histogram(
    "catalog_sync_duration_ms",
    "Catalog sync duration in milliseconds",
)
CATALOG_SYNC_COUNTER = Counter(
    "catalog_sync_runs_total",
    "Catalog sync runs",
    labelnames=("status",),
)


class CatalogSyncRunner:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._last_summary: CatalogSyncSummary | None = None
        self._task_service_base = settings.task_service_internal_url.rstrip("/")

    @property
    def last_summary(self) -> CatalogSyncSummary | None:
        return self._last_summary

    async def trigger(
        self,
        *,
        initiated_by: UUID | None,
        trigger: CatalogSyncTriggerRequest | None = None,
    ) -> CatalogSyncSummary:
        async with self._lock:
            started_at = datetime.now(timezone.utc)
            timer = time.perf_counter()
            summary: CatalogSyncSummary
            source_override = trigger.source if trigger and trigger.source else None
            deactivate_override = (
                trigger.deactivate_missing if trigger and trigger.deactivate_missing is not None else None
            )
            try:
                items = await self._load_items(source_override, trigger.path if trigger else None)
                if not items:
                    raise ValueError("Catalog source returned no items")

                options = CatalogSyncOptions(
                    deactivate_missing=(
                        deactivate_override
                        if deactivate_override is not None
                        else settings.catalog_sync_deactivate_missing
                    ),
                    source=source_override or settings.catalog_sync_source,
                )
                batch = CatalogUpsertBatch(items=items, options=options)
                payload = batch.to_task_payload()

                async with httpx.AsyncClient(timeout=settings.task_service_timeout_seconds) as client:
                    response = await client.post(
                        f"{self._task_service_base}/internal/catalog/upsert-batch",
                        json=payload,
                        headers={"Authorization": f"Bearer {settings.service_token}"},
                    )

                body = response.json()
                if response.status_code not in (200, 202):
                    raise RuntimeError(
                        f"Task service error {response.status_code}: {body if body else response.text}"
                    )

                finished_at = datetime.now(timezone.utc)
                duration_ms = body.get("duration_ms") or (time.perf_counter() - timer) * 1000
                status_label = "cached" if response.status_code == 202 or body.get("cached") else "success"
                summary = CatalogSyncSummary(
                    status=status_label,
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    processed=body.get("processed"),
                    created=body.get("created"),
                    updated=body.get("updated"),
                    deactivated=body.get("deactivated"),
                    cached=bool(body.get("cached")),
                    source=payload["options"].get("source"),
                    payload_hash=payload["options"].get("payload_hash"),
                    message=None,
                )
                logger.info(
                    "catalog.sync.completed",
                    status=summary.status,
                    processed=summary.processed,
                    created=summary.created,
                    updated=summary.updated,
                    deactivated=summary.deactivated,
                    actor=str(initiated_by) if initiated_by else None,
                )
            except Exception as exc:  # noqa: BLE001
                finished_at = datetime.now(timezone.utc)
                duration_ms = (time.perf_counter() - timer) * 1000
                logger.error(
                    "catalog.sync.failed",
                    error=str(exc),
                    actor=str(initiated_by) if initiated_by else None,
                )
                summary = CatalogSyncSummary(
                    status="failed",
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    processed=None,
                    created=None,
                    updated=None,
                    deactivated=None,
                    cached=False,
                    source=source_override or settings.catalog_sync_source,
                    payload_hash=None,
                    message=str(exc),
                )

            self._last_summary = summary
            CATALOG_SYNC_COUNTER.labels(status=summary.status).inc()
            if summary.duration_ms is not None:
                CATALOG_SYNC_DURATION.observe(summary.duration_ms)
            return summary

    async def _load_items(self, source: str | None, path_override: str | None) -> list[CatalogItem]:
        effective_source = (source or settings.catalog_sync_source).upper()
        if effective_source == "FILE":
            return await self._load_from_file(path_override)
        if effective_source == "REST":
            return await self._load_from_rest(path_override)
        raise ValueError(f"Unsupported catalog source: {effective_source}")

    async def _load_from_file(self, path_override: str | None) -> list[CatalogItem]:
        configured = settings.catalog_sync_path
        file_path = Path(path_override) if path_override else configured
        if not file_path:
            raise ValueError("catalog_sync_path is not configured")
        if not file_path.exists():
            raise FileNotFoundError(str(file_path))

        def read_file() -> list[CatalogItem]:
            raw = json.loads(file_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "items" in raw:
                payload = raw["items"]
            else:
                payload = raw
            if not isinstance(payload, list):
                raise ValueError("Invalid catalog file format")
            return [CatalogItem.model_validate(item) for item in payload]

        return await asyncio.to_thread(read_file)

    async def _load_from_rest(self, endpoint_override: str | None) -> list[CatalogItem]:
        endpoint = endpoint_override or settings.catalog_sync_rest_endpoint
        if not endpoint:
            raise ValueError("catalog_sync_rest_endpoint is not configured")
        async with httpx.AsyncClient(timeout=settings.task_service_timeout_seconds) as client:
            response = await client.get(endpoint)
            response.raise_for_status()
            data = response.json()
        payload = data.get("items") if isinstance(data, dict) else data
        if not isinstance(payload, list):
            raise ValueError("REST catalog endpoint must return a list or {\"items\": [...]}")
        return [CatalogItem.model_validate(item) for item in payload]


class CatalogSyncScheduler:
    def __init__(self, runner: CatalogSyncRunner) -> None:
        self._runner = runner
        self._task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(self._run_loop())

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stopped.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:  # noqa: PERF203 - expected on shutdown
            pass
        finally:
            self._task = None
            self._stopped.clear()

    async def _run_loop(self) -> None:
        cron_expression = settings.catalog_sync_cron
        if not cron_expression:
            logger.info("catalog.sync.cron.disabled")
            return

        from croniter import croniter  # imported lazily to avoid dependency if cron disabled

        logger.info("catalog.sync.cron.started", cron=cron_expression)
        while not self._stopped.is_set():
            now = datetime.now(timezone.utc)
            iterator = croniter(cron_expression, now)
            next_run = iterator.get_next(datetime)
            sleep_seconds = max((next_run - now).total_seconds(), 0.0)
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=sleep_seconds)
                if self._stopped.is_set():
                    break
            except asyncio.TimeoutError:
                pass

            try:
                await self._runner.trigger(initiated_by=None)
            except Exception as exc:  # noqa: BLE001
                logger.error("catalog.sync.cron.failed", error=str(exc))

        logger.info("catalog.sync.cron.stopped")


runner = CatalogSyncRunner()
scheduler = CatalogSyncScheduler(runner)


def get_sync_status() -> CatalogStatusResponse:
    return CatalogStatusResponse(last_run=runner.last_summary)
