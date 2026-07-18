"""Repository contracts required by the users domain."""

from typing import Protocol

from app.modules.users.domain.entities import User


class UserRepository(Protocol):
    """Persistence operations required by user use cases."""

    async def add(self, user: User) -> User:
        """Persist and return a new user."""
        ...

    async def get_by_id(self, user_id: str) -> User | None:
        """Return a user by public identifier when it exists."""
        ...

    async def get_by_normalized_email(
        self,
        normalized_email: str,
    ) -> User | None:
        """Return a user by canonical email when it exists."""
        ...
