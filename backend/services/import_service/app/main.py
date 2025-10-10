import asyncio
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from prometheus_fastapi_instrumentator import Instrumentator

from app_common.logging import configure_logging, get_logger

from .config import settings
from .services.processor import ImportProcessor

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="Magacin Import Service", version="0.1.0")
processor = ImportProcessor()

Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.post("/api/import/manual", status_code=status.HTTP_202_ACCEPTED)
async def manual_import(file: UploadFile = File(...)) -> dict[str, str]:
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name required")

    saved_path = await processor.save_upload(file)
    await processor.enqueue_file(saved_path)
    return {"status": "queued", "file": file.filename}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _ensure_directories() -> None:
    for path in [
        settings.import_watch_path,
        settings.import_processed_path,
        settings.import_failed_path,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


async def _watch_loop() -> None:
    logger.info("import-service.watch.start", path=str(settings.import_watch_path))
    while True:
        await processor.scan_watch_path()
        await asyncio.sleep(settings.poll_interval_seconds)


@app.on_event("startup")
async def on_startup() -> None:
    _ensure_directories()
    app.state.watch_task = asyncio.create_task(_watch_loop())
    logger.info("import-service.startup")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    watch_task = getattr(app.state, "watch_task", None)
    if watch_task:
        watch_task.cancel()
    logger.info("import-service.shutdown")
