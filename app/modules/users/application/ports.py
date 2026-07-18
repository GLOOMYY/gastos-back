"""Application ports required by authentication use cases."""

from datetime import datetime
from typing import Protocol

from app.modules.users.application.dto import (
    IssuedRefreshToken,
    IssuedToken,
    RefreshTokenRecord,
    TokenClaims,
)


class PasswordHasher(Protocol):
    """Secure password hashing operations."""

    def hash(self, password: str) -> str:
        """Return a secure one-way password hash."""
        ...

    def verify(self, password: str, password_hash: str) -> bool:
        """Return whether a password matches a stored hash."""
        ...


class TokenService(Protocol):
    """Issue, validate, and fingerprint authentication tokens."""

    def issue_access_token(self, user_id: str) -> IssuedToken:
        """Issue a short-lived access token."""
        ...

    def issue_refresh_token(
        self,
        user_id: str,
        family_id: str,
    ) -> IssuedRefreshToken:
        """Issue a refresh token within a rotation family."""
        ...

    def decode_access_token(self, token: str) -> TokenClaims:
        """Validate an access token and return trusted claims."""
        ...

    def decode_refresh_token(self, token: str) -> TokenClaims:
        """Validate a refresh token and return trusted claims."""
        ...

    def hash_token(self, token: str) -> str:
        """Return a stable one-way token fingerprint."""
        ...


class RefreshTokenRepository(Protocol):
    """Persistence operations for refresh-token rotation state."""

    async def add(self, record: RefreshTokenRecord) -> None:
        """Persist a newly issued refresh token record."""
        ...

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> RefreshTokenRecord | None:
        """Return refresh-token state by its fingerprint."""
        ...

    async def consume(
        self,
        token_hash: str,
        replaced_by_id: str,
        revoked_at: datetime,
    ) -> bool:
        """Atomically revoke an active token during rotation."""
        ...

    async def revoke_by_hash(
        self,
        token_hash: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke a refresh token when it exists and is active."""
        ...

    async def revoke_family(
        self,
        family_id: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke every active token belonging to one family."""
        ...

    async def revoke_by_user(
        self,
        user_id: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke every active refresh token belonging to a user."""
        ...


class Clock(Protocol):
    """Source of timezone-aware current time."""

    def now(self) -> datetime:
        """Return the current time in UTC."""
        ...


class IdGenerator(Protocol):
    """Source of unpredictable public identifiers."""

    def generate(self) -> str:
        """Return a new identifier."""
        ...
