"""Configuration settings for EnergyOracle API."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Supabase
    supabase_url: str
    supabase_service_key: str

    # API
    api_title: str = "EnergyOracle API"
    api_version: str = "0.1.0"
    api_description: str = "UK energy market data for PPA settlement"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore extra fields in .env
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
