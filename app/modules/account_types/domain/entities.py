"""Domain entities for account types."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.account_types.domain.exceptions import (
    InvalidAccountTypeNameError,
    InvalidAccountTypeOwnerError,
)


@dataclass(slots=True)
class AccountType:
    """Global or user-owned classification for financial accounts."""

    id: str | None
    user_id: str | None
    code: str | None
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        description: str | None = None,
        user_id: str | None = None,
        code: str | None = None,
    ) -> "AccountType":
        """Create a global or user-owned account type.

        Args:
            name: Visible account type name.
            description: Optional explanatory text.
            user_id: Owner identifier, or None for a global type.

        Returns:
            A new active account type.

        Raises:
            InvalidAccountTypeNameError: If the name is blank.
            InvalidAccountTypeOwnerError: If the owner is blank.
        """
        clean_name = name.strip()
        if not clean_name:
            raise InvalidAccountTypeNameError()

        clean_user_id = user_id.strip() if user_id is not None else None
        if user_id is not None and not clean_user_id:
            raise InvalidAccountTypeOwnerError()

        clean_description = (
            description.strip() if description and description.strip() else None
        )

        clean_code = code.strip().upper() if code and code.strip() else None
        now = datetime.now(UTC)
        return cls(
            id=None,
            user_id=clean_user_id,
            code=clean_code,
            name=clean_name,
            description=clean_description,
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @property
    def is_global(self) -> bool:
        """Return whether all users may use this account type."""
        return self.user_id is None

    @property
    def normalized_name(self) -> str:
        """Return the canonical name used for comparisons."""
        return self.name.casefold()

    def deactivate(self) -> None:
        """Prevent the account type from being selected."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Allow the account type to be selected."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def update_details(
        self,
        name: str,
        description: str | None,
    ) -> None:
        """Update editable account type details."""
        clean_name = name.strip()
        if not clean_name:
            raise InvalidAccountTypeNameError()
        self.name = clean_name
        self.description = (
            description.strip() if description and description.strip() else None
        )
        self.updated_at = datetime.now(UTC)
