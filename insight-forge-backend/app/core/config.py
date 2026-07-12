"""
Insight Forge V2 — Central Application Configuration.

Loads environment variables using Pydantic Settings.
"""

from functools import lru_cache
from typing import Any
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated, Self
from pydantic import BeforeValidator


def parse_comma_separated_list(v: Any) -> list[str]:
    """Parse comma-separated values or JSON lists into a Python list of strings."""
    if isinstance(v, str):
        if not v.strip():
            return []
        if v.startswith("[") and v.endswith("]"):
            import json

            try:
                return json.loads(v)
            except Exception:
                pass
        return [item.strip() for item in v.split(",") if item.strip()]
    if isinstance(v, list):
        return [str(item).strip() for item in v]
    return []


CommaSeparatedList = Annotated[list[str], BeforeValidator(parse_comma_separated_list)]


class Settings(BaseSettings):
    """Central application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_NAME: str = "Insight Forge"
    APP_VERSION: str = "2.0.0"
    VERSION: str = "2.0.0"
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False

    DATABASE_URL: str = ""
    MIGRATION_DATABASE_URL: str = ""

    SECRET_KEY: str = "default-secret-key-32-characters-long"
    JWT_SECRET: str = "default-secret-key-32-characters-long"
    JWT_SECRET_KEY: str = "default-secret-key-32-characters-long"
    JWT_PRIVATE_KEY_PATH: str = ""
    JWT_PUBLIC_KEY_PATH: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, gt=0)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, gt=0)
    JWT_ISSUER: str = "insight-forge-v2"
    JWT_AUDIENCE: str = "insight-forge-v2-client"

    DB_POOL_SIZE: int = Field(default=20, gt=0)
    DB_MAX_OVERFLOW: int = Field(default=10, ge=0)
    DB_POOL_TIMEOUT: int = Field(default=30, gt=0)
    DB_POOL_RECYCLE: int = Field(default=1800, gt=0)

    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    ALLOWED_HOSTS: CommaSeparatedList = Field(default=["*"])
    CORS_ORIGINS: CommaSeparatedList = Field(default=["*"])

    LOG_LEVEL: str = "INFO"

    @model_validator(mode="after")
    def sync_legacy_fields(self) -> Self:
        """Synchronize alias/legacy configuration fields."""
        # Sync APP_VERSION and VERSION
        if self.APP_VERSION != "2.0.0" and self.VERSION == "2.0.0":
            self.VERSION = self.APP_VERSION
        elif self.VERSION != "2.0.0" and self.APP_VERSION == "2.0.0":
            self.APP_VERSION = self.VERSION

        # Sync APP_ENV and ENVIRONMENT
        if self.APP_ENV != "development" and self.ENVIRONMENT == "development":
            self.ENVIRONMENT = self.APP_ENV
        elif self.ENVIRONMENT != "development" and self.APP_ENV == "development":
            self.APP_ENV = self.ENVIRONMENT

        # Sync SECRET_KEY, JWT_SECRET, and JWT_SECRET_KEY
        secret_val = self.JWT_SECRET_KEY or self.JWT_SECRET or self.SECRET_KEY
        if secret_val:
            self.JWT_SECRET_KEY = secret_val
            self.JWT_SECRET = secret_val
            self.SECRET_KEY = secret_val

        # Enforce minimum key size
        if not self.JWT_SECRET or len(self.JWT_SECRET) < 32:
            raise ValueError(
                "JWT_SECRET (or SECRET_KEY / JWT_SECRET_KEY) must be configured and contain at least 32 characters."
            )

        # Enforce supported algorithms
        if self.JWT_ALGORITHM not in ("HS256", "RS256"):
            raise ValueError(
                f"Unsupported JWT_ALGORITHM: '{self.JWT_ALGORITHM}'. Only HS256 and RS256 are supported."
            )

        # Enforce Issuer & Audience
        if not self.JWT_ISSUER.strip():
            raise ValueError("JWT_ISSUER configuration cannot be empty.")
        if not self.JWT_AUDIENCE.strip():
            raise ValueError("JWT_AUDIENCE configuration cannot be empty.")

        return self

    @property
    def async_database_url(self) -> str:
        """Construct SQLAlchemy-compatible async database URL using psycopg driver."""
        if not self.DATABASE_URL:
            return ""
        if self.DATABASE_URL.startswith("postgresql://"):
            return self.DATABASE_URL.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        return self.DATABASE_URL


@lru_cache
def get_settings() -> Settings:
    """Return one cached Settings instance for the application process."""
    return Settings()


settings = get_settings()
