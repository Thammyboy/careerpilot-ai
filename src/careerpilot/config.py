"""Configuration management for CareerPilot AI using pydantic-settings."""

from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application runtime settings loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Notion Integration
    notion_api_key: Optional[str] = Field(default=None, alias="NOTION_API_KEY")
    notion_database_id: Optional[str] = Field(default=None, alias="NOTION_DATABASE_ID")

    # Paths
    profile_dir: Path = Field(default=Path("profile"), alias="PROFILE_DIR")
    storage_dir: Path = Field(default=Path("storage"), alias="STORAGE_DIR")

    # Scraping Configuration
    scraping_delay_min: float = Field(default=2.0, alias="SCRAPING_DELAY_MIN")
    scraping_delay_max: float = Field(default=6.5, alias="SCRAPING_DELAY_MAX")
    scraping_max_retries: int = Field(default=3, alias="SCRAPING_MAX_RETRIES")
    scraping_request_timeout: float = Field(default=15.0, alias="SCRAPING_REQUEST_TIMEOUT")

    # Deduplication
    deduplication_window_days: int = Field(default=90, alias="DEDUPLICATION_WINDOW_DAYS")

    # Search Defaults
    default_search_keywords: str = Field(
        default="Software Engineer", alias="DEFAULT_SEARCH_KEYWORDS"
    )
    default_search_location: str = Field(
        default="Thailand", alias="DEFAULT_SEARCH_LOCATION"
    )

    def ensure_directories(self) -> None:
        """Ensure that required runtime directories exist."""
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
