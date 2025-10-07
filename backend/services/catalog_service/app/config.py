from __future__ import annotations

from pathlib import Path
from typing import Literal

from app_common.config import Settings as BaseSettings


class Settings(BaseSettings):
    service_name: str = "catalog-service"
    task_service_internal_url: str = "http://task-service:8000"
    task_service_timeout_seconds: float = 30.0
    catalog_sync_source: Literal["FILE", "REST", "SFTP"] = "FILE"
    catalog_sync_path: Path | None = None
    catalog_sync_rest_endpoint: str | None = None
    catalog_sync_deactivate_missing: bool = True
    catalog_sync_cron: str | None = "0 2 * * *"


settings = Settings()
