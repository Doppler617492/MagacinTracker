from app_common.config import Settings as BaseSettings


class Settings(BaseSettings):
    service_name: str = "realtime-worker"
    leaderboard_channel: str = "tv:delta"
    socketio_url: str = "http://api-gateway:8000"


settings = Settings()
