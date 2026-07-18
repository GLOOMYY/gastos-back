"""Use case for ending an authenticated user session."""

from app.modules.users.application.dto import LogoutUserCommand
from app.modules.users.application.ports import (
    Clock,
    RefreshTokenRepository,
    TokenService,
)


class LogoutUser:
    """Revoke the supplied refresh token when it exists."""

    def __init__(
        self,
        refresh_token_repository: RefreshTokenRepository,
        token_service: TokenService,
        clock: Clock,
    ) -> None:
        """Initialize the logout use case."""
        self._refresh_token_repository = refresh_token_repository
        self._token_service = token_service
        self._clock = clock

    async def execute(self, command: LogoutUserCommand) -> None:
        """Revoke a refresh token without revealing whether it existed."""
        await self._refresh_token_repository.revoke_by_hash(
            self._token_service.hash_token(command.refresh_token),
            self._clock.now(),
        )
