"""Pydantic HTTP schemas for user authentication."""

from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RegisterUserRequest(BaseModel):
    """Public user registration request."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    """Email and password login request."""

    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)


class RefreshSessionRequest(BaseModel):
    """Refresh-token rotation request."""

    refresh_token: str = Field(min_length=1, max_length=4096)


class LogoutRequest(BaseModel):
    """Refresh-token revocation request."""

    refresh_token: str = Field(min_length=1, max_length=4096)


class UpdateUserRequest(BaseModel):
    """Supported changes to the authenticated user."""

    email: str | None = Field(default=None, min_length=3, max_length=254)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    name: str | None = Field(default=None, min_length=1, max_length=120)
    favorite_currency: str | None = Field(
        default=None,
        min_length=3,
        max_length=10,
    )
    country_code: str | None = Field(default=None, min_length=2, max_length=2)

    @model_validator(mode="after")
    def require_at_least_one_change(self) -> Self:
        """Reject update requests without a supported field."""
        if all(
            value is None
            for value in (
                self.email,
                self.password,
                self.name,
                self.favorite_currency,
                self.country_code,
            )
        ):
            raise ValueError("At least one user field must be updated.")
        return self


class UserResponse(BaseModel):
    """Safe public representation of a user."""

    id: str
    email: str
    role: str
    name: str | None
    favorite_currency: str | None
    country_code: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenPairResponse(BaseModel):
    """Access and refresh tokens issued to an authenticated client."""

    access_token: str
    refresh_token: str
    token_type: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime

    model_config = ConfigDict(from_attributes=True)
