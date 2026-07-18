"""Use case for retrieving a user by identifier."""

from app.modules.users.application.dto import UserResult
from app.modules.users.application.mappers import user_to_result
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    UserNotFoundError,
)
from app.modules.users.domain.repositories import UserRepository


class GetUser:
    """Retrieve an active user for an authenticated request."""

    def __init__(self, user_repository: UserRepository) -> None:
        """Initialize the user query."""
        self._user_repository = user_repository

    async def execute(self, user_id: str) -> UserResult:
        """Return an active user by public identifier."""
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError()
        if not user.is_active:
            raise InactiveUserError()
        return user_to_result(user)
