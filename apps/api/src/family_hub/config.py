"""Application settings, loaded from environment variables (prefix ``FH_``)."""

from datetime import timedelta
from functools import lru_cache
from typing import Literal, Self

from pydantic import PostgresDsn, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEV_SECRET = "dev-only-insecure-secret-change-me"  # noqa: S105 - rejected in production


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

    secret_key: SecretStr = SecretStr(INSECURE_DEV_SECRET)
    """Key for deriving CSRF tokens. Must be set to a long random value in production."""

    cookie_secure: bool = True
    """Mark cookies ``Secure`` and use the ``__Host-`` prefix. Disable only for plain-HTTP dev."""

    session_idle_timeout: timedelta = timedelta(days=14)
    """A session unused for this long expires (AUTH-6)."""

    session_absolute_timeout: timedelta = timedelta(days=60)
    """A session expires this long after login, regardless of use (AUTH-6)."""

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @model_validator(mode="after")
    def _production_safety(self) -> Self:
        if self.is_production:
            secret = self.secret_key.get_secret_value()
            if secret == INSECURE_DEV_SECRET or len(secret) < 32:
                raise ValueError("FH_SECRET_KEY must be set to at least 32 random characters")
            if not self.cookie_secure:
                raise ValueError("FH_COOKIE_SECURE must be true in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
