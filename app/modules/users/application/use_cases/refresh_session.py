"""Use case for rotating an authenticated user session."""

from app.modules.users.application.dto import (
    RefreshSessionCommand,
    RefreshTokenRecord,
    TokenClaims,
    TokenPairResult,
)
from app.modules.users.application.ports import (
    Clock,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    InvalidAuthenticationTokenError,
)
from app.modules.users.domain.repositories import UserRepository


class RefreshSession:
    """Rotate a valid refresh token and detect token reuse."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        clock: Clock,
    ) -> None:
        """Initialize the refresh session use case."""
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._token_service = token_service
        self._clock = clock

    async def execute(
        self,
        command: RefreshSessionCommand,
    ) -> TokenPairResult:
        """Consume a refresh token and return a rotated token pair."""
        claims = self._token_service.decode_refresh_token(
            command.refresh_token,
        )
        if claims.family_id is None:
            raise InvalidAuthenticationTokenError()

        now = self._clock.now()
        token_hash = self._token_service.hash_token(command.refresh_token)
        record = await self._refresh_token_repository.get_by_hash(token_hash)

        if record is None or not self._record_matches_claims(record, claims):
            raise InvalidAuthenticationTokenError()

        if record.revoked_at is not None:
            await self._refresh_token_repository.revoke_family(
                record.family_id,
                now,
            )
            raise InvalidAuthenticationTokenError()

        if record.expires_at <= now:
            raise InvalidAuthenticationTokenError()

        user = await self._user_repository.get_by_id(record.user_id)
        if user is None:
            await self._refresh_token_repository.revoke_family(
                record.family_id,
                now,
            )
            raise InvalidAuthenticationTokenError()
        if not user.is_active:
            await self._refresh_token_repository.revoke_family(
                record.family_id,
                now,
            )
            raise InactiveUserError()

        access_token = self._token_service.issue_access_token(record.user_id)
        refresh_token = self._token_service.issue_refresh_token(
            record.user_id,
            record.family_id,
        )

        consumed = await self._refresh_token_repository.consume(
            token_hash=record.token_hash,
            replaced_by_id=refresh_token.token_id,
            revoked_at=now,
        )
        if not consumed:
            await self._refresh_token_repository.revoke_family(
                record.family_id,
                now,
            )
            raise InvalidAuthenticationTokenError()

        await self._refresh_token_repository.add(
            RefreshTokenRecord(
                id=refresh_token.token_id,
                user_id=record.user_id,
                token_hash=self._token_service.hash_token(
                    refresh_token.value,
                ),
                family_id=record.family_id,
                expires_at=refresh_token.expires_at,
                revoked_at=None,
                replaced_by_id=None,
                created_at=now,
            )
        )

        return TokenPairResult(
            access_token=access_token.value,
            refresh_token=refresh_token.value,
            access_token_expires_at=access_token.expires_at,
            refresh_token_expires_at=refresh_token.expires_at,
        )

    @staticmethod
    def _record_matches_claims(
        record: RefreshTokenRecord,
        claims: TokenClaims,
    ) -> bool:
        """Return whether persisted state matches validated token claims."""
        return (
            record.id == claims.token_id
            and record.user_id == claims.user_id
            and record.family_id == claims.family_id
        )
