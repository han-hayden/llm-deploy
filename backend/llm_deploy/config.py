"""Application configuration using pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = "sqlite+aiosqlite:///./llm_deploy.sqlite"
    UPLOAD_DIR: str = "./uploads"
    MODELS_CACHE_DIR: str = "./models_cache"
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # HuggingFace settings
    HF_TOKEN: str = ""
    HF_MIRROR: str = ""

    # ModelScope settings
    MS_TOKEN: str = ""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
