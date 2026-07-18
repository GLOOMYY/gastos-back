"""Use case for deactivating the authenticated user."""

from app.modules.users.application.dto import DeactivateUserCommand
from app.modules.users.application.ports import Clock, RefreshTokenRepository
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    UserNotFoundError,
)
from app.modules.users.domain.repositories import UserRepository


class DeactivateUser:
    """Soft-delete a user and revoke all refresh-token sessions."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        clock: Clock,
    ) -> None:
        """Initialize the user deactivation use case."""
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._clock = clock

    async def execute(self, command: DeactivateUserCommand) -> None:
        """Deactivate the user without deleting financial history."""
        user = await self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError()
        if not user.is_active:
            raise InactiveUserError()

        user.deactivate()
        await self._user_repository.update(user)
        await self._refresh_token_repository.revoke_by_user(
            command.user_id,
            self._clock.now(),
        )
