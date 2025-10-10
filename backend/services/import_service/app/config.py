from pathlib import Path

from app_common.config import Settings as BaseSettings


class Settings(BaseSettings):
    service_name: str = "import-service"
    import_watch_path: Path = Path("/import")
    import_processed_path: Path = Path("/import/processed")
    import_failed_path: Path = Path("/import/failed")
    poll_interval_seconds: int = 60
    task_service_url: str = "http://task-service:8001"
    task_service_internal_url: str = "http://task-service:8001"
    task_service_timeout_seconds: float = 30.0
    service_user_id: str = "00000000-0000-0000-0000-000000000001"
    service_token: str = "service-local"


settings = Settings()
