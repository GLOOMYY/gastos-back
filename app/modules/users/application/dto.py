"""Commands and results for user application use cases."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CreateUserCommand:
    """Data required to register a user."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class AuthenticateUserCommand:
    """Credentials used to start an authenticated session."""

    email: str
    password: str


@dataclass(frozen=True, slots=True)
class RefreshSessionCommand:
    """Refresh token used to rotate an authenticated session."""

    refresh_token: str


@dataclass(frozen=True, slots=True)
class LogoutUserCommand:
    """Refresh token whose session must be revoked."""

    refresh_token: str


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    """Changes requested by the authenticated user."""

    user_id: str
    email: str | None = None
    password: str | None = None
    favorite_currency: str | None = None
    country_code: str | None = None


@dataclass(frozen=True, slots=True)
class DeactivateUserCommand:
    """Authenticated user whose account must be deactivated."""

    user_id: str


@dataclass(frozen=True, slots=True)
class UserResult:
    """Safe user information returned by application use cases."""

    id: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    favorite_currency: str | None = None
    country_code: str | None = None


@dataclass(frozen=True, slots=True)
class IssuedToken:
    """Token value and its absolute expiration."""

    value: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class IssuedRefreshToken:
    """Refresh token value and identifiers needed for rotation."""

    value: str
    token_id: str
    family_id: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class TokenClaims:
    """Validated authentication token claims."""

    user_id: str
    token_id: str
    expires_at: datetime
    family_id: str | None = None


@dataclass(frozen=True, slots=True)
class TokenPairResult:
    """Access and refresh tokens returned to an authenticated client."""

    access_token: str
    refresh_token: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    token_type: str = "bearer"


@dataclass(frozen=True, slots=True)
class RefreshTokenRecord:
    """Persisted server-side state for a refresh token."""

    id: str
    user_id: str
    token_hash: str
    family_id: str
    expires_at: datetime
    revoked_at: datetime | None
    replaced_by_id: str | None
    created_at: datetime
