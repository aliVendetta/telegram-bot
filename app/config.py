"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation via Pydantic."""

    # Telegram
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_webhook_secret: str = Field(
        ..., description="Secret token for webhook validation"
    )

    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./notes.db",
        description="Async database connection URL",
    )

    # Notion
    notion_token: str = Field(..., description="Notion integration token")
    notion_database_id: str = Field(..., description="Notion database ID")

    # Application
    app_env: str = Field(default="development", description="Application environment")
    log_level: str = Field(default="INFO", description="Logging level")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
