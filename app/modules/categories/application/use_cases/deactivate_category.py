"""Deactivate a user-owned category."""

from app.modules.categories.domain.exceptions import (
    CategoryAccessDeniedError,
    CategoryNotFoundError,
)
from app.modules.categories.domain.repositories import CategoryRepository


class DeactivateCategory:
    """Soft-delete an owned category."""

    def __init__(self, repository: CategoryRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, category_id: str) -> None:
        """Deactivate an owned category while preserving ledger references."""
        category = await self._repository.get_by_id(category_id)
        if category is None:
            raise CategoryNotFoundError()
        if category.user_id != user_id:
            raise CategoryAccessDeniedError()
        category.deactivate()
        await self._repository.update(category)
