from typing import List, Optional

from pydantic import Field, field_validator
from app_common.config import Settings as BaseSettings


class Settings(BaseSettings):
    api_prefix: str = "/api"
    task_service_url: str = "http://task-service:8001"
    catalog_service_url: str = "http://catalog-service:8002"
    import_service_url: str = "http://import-service:8003"
    # Device auth settings
    device_secret: Optional[str] = None
    device_allowlist: List[str] = Field(default_factory=list)
    device_token_rate_limit_per_min: int = 60

    def __init__(self, **data):
        super().__init__(**data)
        if not self.cors_origins:
            self.cors_origins = [
                "http://localhost:5173", 
                "http://localhost:4173", 
                "http://localhost:5130",
                "http://localhost:3000"
            ]

    @field_validator("device_allowlist", mode="before")
    @classmethod
    def split_allowlist(cls, value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value


settings = Settings()
