import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/magacin")
    
    # AI Model Configuration
    model_save_path: str = os.getenv("MODEL_SAVE_PATH", "./models")
    training_batch_size: int = int(os.getenv("TRAINING_BATCH_SIZE", "32"))
    training_epochs: int = int(os.getenv("TRAINING_EPOCHS", "100"))
    learning_rate: float = float(os.getenv("LEARNING_RATE", "0.001"))
    
    # Reinforcement Learning
    rl_epsilon: float = float(os.getenv("RL_EPSILON", "0.1"))
    rl_learning_rate: float = float(os.getenv("RL_LEARNING_RATE", "0.01"))
    rl_discount_factor: float = float(os.getenv("RL_DISCOUNT_FACTOR", "0.95"))
    
    # Performance
    prediction_timeout: int = int(os.getenv("PREDICTION_TIMEOUT", "500"))
    training_timeout: int = int(os.getenv("TRAINING_TIMEOUT", "60000"))
    
    # Security
    api_key: str = os.getenv("AI_ENGINE_API_KEY", "ai-engine-secret-key")
    
    class Config:
        env_file = ".env"


settings = Settings()
