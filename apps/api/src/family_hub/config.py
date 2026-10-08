"""Application settings, loaded from environment variables (prefix ``FH_``)."""

from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FH_", env_file=".env", extra="ignore")

    environment: Literal["development", "test", "production"] = "development"
    """Deployment environment. Controls docs exposure and other safety switches."""

    database_url: PostgresDsn = PostgresDsn(
        "postgresql+asyncpg://family_hub:family_hub@localhost:5432/family_hub"
    )
    """SQLAlchemy URL for PostgreSQL, using the asyncpg driver."""

    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    """Redis URL for rate limits and policy notifications."""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
