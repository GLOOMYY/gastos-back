"""Repository contract for account types."""

from typing import Protocol

from app.modules.account_types.domain.entities import AccountType


class AccountTypeRepository(Protocol):
    """Persistence operations required by account type use cases."""

    async def add(self, account_type: AccountType) -> AccountType:
        """Persist a new account type."""
        ...

    async def get_by_id(self, account_type_id: str) -> AccountType | None:
        """Return an account type by identifier."""
        ...

    async def list_available(self, user_id: str) -> list[AccountType]:
        """Return active global and user-owned account types."""
        ...

    async def exists_name(
        self,
        user_id: str | None,
        normalized_name: str,
        excluding_id: str | None = None,
    ) -> bool:
        """Check name uniqueness within one ownership scope."""
        ...

    async def update(self, account_type: AccountType) -> AccountType:
        """Persist and return changes to an account type."""
        ...
