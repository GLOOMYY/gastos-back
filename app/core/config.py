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
    cors_allowed_origins: str = ""

    mongodb_uri: SecretStr | None = None
    mongodb_database: str | None = None
    mongodb_server_selection_timeout_ms: int = Field(default=10000, gt=0)

    jwt_secret_key: SecretStr | None = None
    jwt_algorithm: Literal["HS256"] = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)
    refresh_token_expire_days: int = Field(default=30, gt=0)

    initial_user_email: str | None = None
    initial_user_password: SecretStr | None = None
    initial_account_name: str = "Main account"
    initial_account_currency: str = "COP"
    initial_account_balance: Decimal = Decimal("0")

    exchange_rate_provider: str = "exchangerate_api"
    exchange_rate_api_key: SecretStr | None = None
    exchange_rate_base_url: str = "https://v6.exchangerate-api.com"
    exchange_rate_timeout_seconds: float = Field(default=5.0, gt=0)
    exchange_rate_cache_ttl_seconds: int = Field(default=300, ge=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_cors_origins(self) -> list[str]:
        """Return normalized browser origins configured as CSV."""
        return [
            origin.strip().rstrip("/")
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]

    def validate_production_configuration(self) -> None:
        """Fail startup when required production settings are unsafe."""
        if self.environment.casefold() != "production":
            return
        missing: list[str] = []
        if self.mongodb_uri is None or not self.mongodb_uri.get_secret_value().strip():
            missing.append("MONGODB_URI")
        if self.mongodb_database is None or not self.mongodb_database.strip():
            missing.append("MONGODB_DATABASE")
        if self.jwt_secret_key is None:
            missing.append("JWT_SECRET_KEY")
        elif len(self.jwt_secret_key.get_secret_value()) < 32:
            raise RuntimeError("JWT_SECRET_KEY must contain at least 32 characters.")
        if self.debug:
            raise RuntimeError("DEBUG must be false in production.")
        if "*" in self.allowed_cors_origins:
            raise RuntimeError("Wildcard CORS origins are not allowed in production.")
        if self.exchange_rate_provider.strip().casefold() not in {
            "exchangerate_api",
            "exchangerate-api",
        }:
            raise RuntimeError("EXCHANGE_RATE_PROVIDER is not supported.")
        if (
            self.exchange_rate_api_key is None
            or not self.exchange_rate_api_key.get_secret_value().strip()
        ):
            missing.append("EXCHANGE_RATE_API_KEY")
        if missing:
            raise RuntimeError(
                f"Missing required production settings: {', '.join(missing)}."
            )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
