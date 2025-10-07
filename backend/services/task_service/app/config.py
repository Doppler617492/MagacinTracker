from app_common.config import Settings as BaseSettings


class Settings(BaseSettings):
    service_name: str = "task-service"


settings = Settings()
