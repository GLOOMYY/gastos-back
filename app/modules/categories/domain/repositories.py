"""Repository contract for financial categories."""

from typing import Protocol

from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.enums import CategoryTransactionType


class CategoryRepository(Protocol):
    """Persistence operations required by category use cases."""

    async def add(self, category: Category) -> Category:
        """Persist a new category."""
        ...

    async def get_by_id(self, category_id: str) -> Category | None:
        """Return a category by identifier."""
        ...

    async def list_available(
        self,
        user_id: str,
        transaction_type: CategoryTransactionType | None = None,
    ) -> list[Category]:
        """Return active global and user-owned categories."""
        ...

    async def exists_name(
        self,
        user_id: str | None,
        normalized_name: str,
        transaction_type: CategoryTransactionType,
        excluding_id: str | None = None,
    ) -> bool:
        """Check category name uniqueness within an ownership scope."""
        ...

    async def update(self, category: Category) -> Category:
        """Persist and return changes to a category."""
        ...
