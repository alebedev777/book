from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = ""
    mini_app_url: str = "http://localhost:5173/"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_chat_model: str = "gpt-4o"
    openai_vision_model: str = ""
    openai_image_model: str = "gpt-image-1"
    moderate_custom_themes: bool = True
    moderate_story_text: bool = False

    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_base_url: str = Field(
        default="",
        validation_alias=AliasChoices("LANGFUSE_BASE_URL", "LANGFUSE_HOST"),
    )

    database_url: str = "postgresql+asyncpg://book:book@localhost:5432/book"
    database_url_sync: str = "postgresql://book:book@localhost:5432/book"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "book-assets"
    s3_public_url: str = "http://localhost:9000/book-assets"

    api_public_url: str = "http://localhost:8000"
    photo_ttl_days: int = 30
    max_pages: int = 10
    mvp_pages: int = 4
    rate_limit_active_orders: int = 1

    shared_dir: Path = _REPO_ROOT / "shared"
    prompt_version: str = "v3"


@lru_cache
def get_settings() -> Settings:
    return Settings()