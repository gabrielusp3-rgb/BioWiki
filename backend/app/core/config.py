"""Application settings loaded from environment / .env."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    project_name: str = Field(default="BIOWIKI API", alias="PROJECT_NAME")
    api_version: str = Field(default="0.1.0", alias="API_VERSION")
    environment: str = Field(default="development", alias="BIOWIKI_ENV")

    database_url: str = Field(
        default="postgresql+asyncpg://biowiki:biowiki@localhost:5432/biowiki",
        alias="DATABASE_URL",
    )
    sql_echo: bool = Field(default=False, alias="SQL_ECHO")
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")

    # CORS — comma separated list of allowed origins for the frontend.
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_requests: int = Field(default=120, alias="RATE_LIMIT_REQUESTS")
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # Comma-separated API keys; empty means the API is open (local development).
    api_keys: str = Field(default="", alias="API_KEYS")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def api_keys_list(self) -> list[str]:
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
