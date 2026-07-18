"""Repository abstractions required by the accounts domain."""

from typing import Protocol

from app.modules.accounts.domain.entities import Account


class AccountRepository(Protocol):
    """Persistence operations for accounts."""

    async def add(self, account: Account) -> Account:
        """Persist and return a new account."""
        ...

    async def get_by_id(self, account_id: str) -> Account | None:
        """Retrieve an account by public identifier."""
        ...

    async def list_by_user(self, user_id: str) -> list[Account]:
        """List a user's accounts."""
        ...

    async def exists_name(
        self,
        user_id: str,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Check active account-name uniqueness for a user."""
        ...

    async def update(self, account: Account) -> Account:
        """Persist an account's mutable state."""
        ...
