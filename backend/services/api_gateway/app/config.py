from app_common.config import Settings as BaseSettings


class Settings(BaseSettings):
    api_prefix: str = "/api"
    task_service_url: str = "http://task-service:8001"
    catalog_service_url: str = "http://catalog-service:8002"
    import_service_url: str = "http://import-service:8003"

    def __init__(self, **data):
        super().__init__(**data)
        if not self.cors_origins:
            self.cors_origins = [
                "http://localhost:5173", 
                "http://localhost:4173", 
                "http://localhost:5130",
                "http://localhost:3000"
            ]


settings = Settings()
