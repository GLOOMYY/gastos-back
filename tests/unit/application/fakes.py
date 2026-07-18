"""Reusable in-memory test doubles for user application use cases."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.modules.users.application.dto import (
    IssuedRefreshToken,
    IssuedToken,
    RefreshTokenRecord,
    TokenClaims,
)
from app.modules.users.domain.entities import User
from app.modules.users.domain.exceptions import (
    InvalidAuthenticationTokenError,
    UserAlreadyExistsError,
)


class FakeUserRepository:
    """Store users in memory by identifier and normalized email."""

    def __init__(self) -> None:
        """Initialize empty user storage."""
        self.users: dict[str, User] = {}
        self._next_id = 1

    async def add(self, user: User) -> User:
        """Assign an identifier and store a user."""
        if await self.get_by_normalized_email(user.email.normalized):
            raise UserAlreadyExistsError()
        user.id = f"user-{self._next_id}"
        self._next_id += 1
        self.users[user.id] = user
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        """Return a stored user by identifier."""
        return self.users.get(user_id)

    async def get_by_normalized_email(
        self,
        normalized_email: str,
    ) -> User | None:
        """Return a stored user by normalized email."""
        return next(
            (
                user
                for user in self.users.values()
                if user.email.normalized == normalized_email
            ),
            None,
        )

    async def update(self, user: User) -> None:
        """Persist changes to an existing in-memory user."""
        if user.id is None or user.id not in self.users:
            return
        duplicate = next(
            (
                existing_user
                for user_id, existing_user in self.users.items()
                if user_id != user.id
                and existing_user.email.normalized == user.email.normalized
            ),
            None,
        )
        if duplicate is not None:
            raise UserAlreadyExistsError()
        self.users[user.id] = user


class FakePasswordHasher:
    """Provide deterministic hashes for application tests."""

    def __init__(self) -> None:
        """Initialize hash invocation tracking."""
        self.hash_calls = 0

    def hash(self, password: str) -> str:
        """Return a deterministic fake password hash."""
        self.hash_calls += 1
        return f"hashed:{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        """Compare a password with the deterministic fake hash."""
        return password_hash == f"hashed:{password}"


class FakeClock:
    """Return a fixed current time."""

    def __init__(self) -> None:
        """Initialize the fixed timestamp."""
        self.current = datetime(2026, 7, 17, 12, 0, tzinfo=UTC)

    def now(self) -> datetime:
        """Return the fixed current time."""
        return self.current


class FakeIdGenerator:
    """Return deterministic identifiers."""

    def __init__(self) -> None:
        """Initialize the identifier counter."""
        self.counter = 0

    def generate(self) -> str:
        """Return the next deterministic identifier."""
        self.counter += 1
        return f"family-{self.counter}"


class FakeTokenService:
    """Issue deterministic tokens and retain their trusted claims."""

    def __init__(self, clock: FakeClock) -> None:
        """Initialize empty token claim storage."""
        self._clock = clock
        self._counter = 0
        self.access_claims: dict[str, TokenClaims] = {}
        self.refresh_claims: dict[str, TokenClaims] = {}

    def issue_access_token(self, user_id: str) -> IssuedToken:
        """Issue a deterministic fake access token."""
        self._counter += 1
        value = f"access-{self._counter}"
        expires_at = self._clock.now() + timedelta(minutes=30)
        self.access_claims[value] = TokenClaims(
            user_id=user_id,
            token_id=f"access-id-{self._counter}",
            expires_at=expires_at,
        )
        return IssuedToken(value=value, expires_at=expires_at)

    def issue_refresh_token(
        self,
        user_id: str,
        family_id: str,
    ) -> IssuedRefreshToken:
        """Issue a deterministic fake refresh token."""
        self._counter += 1
        value = f"refresh-{self._counter}"
        token_id = f"refresh-id-{self._counter}"
        expires_at = self._clock.now() + timedelta(days=30)
        self.refresh_claims[value] = TokenClaims(
            user_id=user_id,
            token_id=token_id,
            expires_at=expires_at,
            family_id=family_id,
        )
        return IssuedRefreshToken(
            value=value,
            token_id=token_id,
            family_id=family_id,
            expires_at=expires_at,
        )

    def decode_access_token(self, token: str) -> TokenClaims:
        """Return stored access claims or reject the token."""
        try:
            return self.access_claims[token]
        except KeyError as error:
            raise InvalidAuthenticationTokenError() from error

    def decode_refresh_token(self, token: str) -> TokenClaims:
        """Return stored refresh claims or reject the token."""
        try:
            return self.refresh_claims[token]
        except KeyError as error:
            raise InvalidAuthenticationTokenError() from error

    def hash_token(self, token: str) -> str:
        """Return the same token fingerprint as production."""
        return sha256(token.encode()).hexdigest()


class FakeRefreshTokenRepository:
    """Store refresh-token records and rotation state in memory."""

    def __init__(self) -> None:
        """Initialize empty refresh-token storage."""
        self.records: dict[str, RefreshTokenRecord] = {}

    async def add(self, record: RefreshTokenRecord) -> None:
        """Store a refresh-token record by fingerprint."""
        self.records[record.token_hash] = record

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> RefreshTokenRecord | None:
        """Return stored refresh-token state."""
        return self.records.get(token_hash)

    async def consume(
        self,
        token_hash: str,
        replaced_by_id: str,
        revoked_at: datetime,
    ) -> bool:
        """Consume an active, non-expired token atomically in memory."""
        record = self.records.get(token_hash)
        if (
            record is None
            or record.revoked_at is not None
            or record.expires_at <= revoked_at
        ):
            return False
        self.records[token_hash] = replace(
            record,
            revoked_at=revoked_at,
            replaced_by_id=replaced_by_id,
        )
        return True

    async def revoke_by_hash(
        self,
        token_hash: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke one active token when present."""
        record = self.records.get(token_hash)
        if record is not None and record.revoked_at is None:
            self.records[token_hash] = replace(
                record,
                revoked_at=revoked_at,
            )

    async def revoke_family(
        self,
        family_id: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke all active tokens in a family."""
        for token_hash, record in tuple(self.records.items()):
            if record.family_id == family_id and record.revoked_at is None:
                self.records[token_hash] = replace(
                    record,
                    revoked_at=revoked_at,
                )

    async def revoke_by_user(
        self,
        user_id: str,
        revoked_at: datetime,
    ) -> None:
        """Revoke every active token belonging to a user."""
        for token_hash, record in tuple(self.records.items()):
            if record.user_id == user_id and record.revoked_at is None:
                self.records[token_hash] = replace(
                    record,
                    revoked_at=revoked_at,
                )
