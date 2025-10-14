from __future__ import annotations

import asyncio
import shutil
import uuid
from pathlib import Path

import httpx
from fastapi import UploadFile

from app_common.logging import get_logger

from ..config import settings
from ..parsers import parse_csv, parse_excel, parse_pdf

logger = get_logger(__name__)

SUPPORTED_EXTENSIONS = {
    ".csv": parse_csv,
    ".xlsx": parse_excel,
    ".xlsm": parse_excel,
    ".pdf": parse_pdf,
}


class ImportProcessor:
    async def save_upload(self, file: UploadFile) -> Path:
        target = settings.import_watch_path / f"{uuid.uuid4()}_{file.filename}"
        with target.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return target

    async def enqueue_file(self, file_path: Path) -> None:
        await self._process_file(file_path)

    async def scan_watch_path(self) -> None:
        for path in settings.import_watch_path.glob("*"):
            if path.is_file():
                await self._process_file(path)

    def _parse_file(self, path: Path) -> dict:
        parser = SUPPORTED_EXTENSIONS.get(path.suffix.lower())
        if not parser:
            raise ValueError(f"Nepodržan format fajla: {path.suffix}")
        payload = parser(path)
        payload.setdefault("meta", {})["source_file"] = path.name
        return payload

    async def _process_file(self, path: Path) -> None:
        logger.info("import.process.start", file=str(path))
        try:
            payload = await asyncio.get_running_loop().run_in_executor(None, self._parse_file, path)
            await self._enrich_payload(payload)

            async with httpx.AsyncClient(timeout=settings.task_service_timeout_seconds) as client:
                response = await client.post(
                    f"{settings.task_service_url}/api/trebovanja/import",
                    json=payload,
                    headers={
                        "X-User-Id": settings.service_user_id,
                        "X-User-Roles": "komercijalista",
                    },
                )
            if response.status_code in (201, 200):
                self._move(path, settings.import_processed_path)
                logger.info("import.process.success", file=str(path))
            elif response.status_code == 400 and "Dokument" in response.text:
                self._move(path, settings.import_processed_path)
                logger.warning("import.process.duplicate", file=str(path))
            else:
                raise ValueError(f"Task service error: {response.status_code} {response.text}")
        except Exception as exc:  # noqa: BLE001
            logger.error("import.process.failed", file=str(path), error=str(exc))
            self._move(path, settings.import_failed_path)

    @staticmethod
    def _move(src: Path, dest_dir: Path) -> None:
        dest_dir.mkdir(parents=True, exist_ok=True)
        target = dest_dir / src.name
        if target.exists():
            target.unlink()
        shutil.move(src, target)

    async def _enrich_payload(self, payload: dict) -> None:
        items = payload.get("stavke")
        if not items:
            return

        base_url = settings.task_service_internal_url.rstrip("/")
        headers = {"Authorization": f"Bearer {settings.service_token}"}
        
        enriched = 0
        upserted = 0

        async with httpx.AsyncClient(timeout=settings.task_service_timeout_seconds) as client:
            for item in items:
                sifra = item.get("artikl_sifra")
                if not sifra:
                    item["needs_barcode"] = True
                    continue

                # Step 1: Lookup existing article
                response = await client.get(
                    f"{base_url}/internal/catalog/lookup",
                    params={"sifra": sifra},
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()

                artikal_id = data.get("artikal_id")
                
                # Step 2: If article doesn't exist, create it
                if not artikal_id:
                    logger.info("import.enrich.upsert_article", sifra=sifra, naziv=item.get("naziv"))
                    upsert_payload = {
                        "items": [
                            {
                                "sifra": sifra,
                                "naziv": item.get("naziv") or sifra,
                                "jedinica_mjere": None,  # Will default to "kom" in backend
                                "barkodovi": [],
                                "aktivan": True,
                            }
                        ],
                        "options": {
                            "source": "import",
                            "deactivate_missing": False,
                        },
                    }
                    
                    # Add barcode if present in CSV
                    if item.get("barkod"):
                        upsert_payload["items"][0]["barkodovi"] = [
                            {"value": item["barkod"], "is_primary": True}
                        ]
                    
                    upsert_response = await client.post(
                        f"{base_url}/internal/catalog/upsert-batch",
                        json=upsert_payload,
                        headers=headers,
                    )
                    upsert_response.raise_for_status()
                    upserted += 1
                    
                    # Re-lookup to get the created article ID
                    lookup_response = await client.get(
                        f"{base_url}/internal/catalog/lookup",
                        params={"sifra": sifra},
                        headers=headers,
                    )
                    lookup_response.raise_for_status()
                    data = lookup_response.json()
                    artikal_id = data.get("artikal_id")

                # Step 3: Enrich the item with catalog data
                if artikal_id:
                    item["artikl_id"] = artikal_id
                    enriched += 1

                primary_barcode = next(
                    (
                        barkod.get("value")
                        for barkod in data.get("barkodovi", [])
                        if barkod.get("is_primary")
                    ),
                    None,
                )
                if primary_barcode is None and data.get("barkodovi"):
                    primary_barcode = data["barkodovi"][0].get("value")

                if not item.get("barkod") and primary_barcode:
                    item["barkod"] = primary_barcode

                item["needs_barcode"] = not bool(item.get("barkod"))
        
        logger.info("import.enrich.complete", enriched=enriched, upserted=upserted, total=len(items))
