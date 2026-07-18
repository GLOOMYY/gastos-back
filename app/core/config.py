"""Environment-based application configuration."""

from decimal import Decimal
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration loaded from environment variables and local `.env`."""

    app_name: str = "Gastos API"
    environment: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    mongodb_uri: SecretStr | None = None
    mongodb_database: str | None = None

    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=30, gt=0)

    initial_user_email: str | None = None
    initial_user_password: SecretStr | None = None
    initial_account_name: str = "Main account"
    initial_account_currency: str = "COP"
    initial_account_balance: Decimal = Decimal("0")

    exchange_rate_provider: str | None = None
    exchange_rate_api_key: SecretStr | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
