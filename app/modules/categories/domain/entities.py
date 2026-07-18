"""Domain entities for financial categories."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.domain.exceptions import (
    InvalidCategoryNameError,
    InvalidCategoryOwnerError,
)


@dataclass(slots=True)
class Category:
    """Global or user-owned classification for financial transactions."""

    id: str | None
    user_id: str | None
    name: str
    transaction_type: CategoryTransactionType
    description: str | None
    is_active: bool
    created_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        transaction_type: CategoryTransactionType,
        description: str | None = None,
        user_id: str | None = None,
    ) -> "Category":
        """Create a global or user-owned category.

        Args:
            name: Visible category name.
            transaction_type: Whether the category classifies income or expense.
            description: Optional explanatory text.
            user_id: Owner identifier, or None for a global category.

        Returns:
            A new active category.

        Raises:
            InvalidCategoryNameError: If the name is blank.
            InvalidCategoryOwnerError: If the owner is blank.
        """
        clean_name = name.strip()
        if not clean_name:
            raise InvalidCategoryNameError()

        clean_user_id = user_id.strip() if user_id is not None else None
        if user_id is not None and not clean_user_id:
            raise InvalidCategoryOwnerError()

        clean_description = (
            description.strip() if description and description.strip() else None
        )

        return cls(
            id=None,
            user_id=clean_user_id,
            name=clean_name,
            transaction_type=transaction_type,
            description=clean_description,
            is_active=True,
            created_at=datetime.now(UTC),
        )

    @property
    def is_global(self) -> bool:
        """Return whether all users may use this category."""
        return self.user_id is None

    @property
    def normalized_name(self) -> str:
        """Return the canonical category name used for comparisons."""
        return self.name.casefold()

    def deactivate(self) -> None:
        """Prevent the category from being selected."""
        self.is_active = False

    def activate(self) -> None:
        """Allow the category to be selected."""
        self.is_active = True
