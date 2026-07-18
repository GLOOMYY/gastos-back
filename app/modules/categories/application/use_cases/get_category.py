"""Retrieve an available category."""

from app.modules.categories.application.dto import CategoryResult
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.exceptions import CategoryNotFoundError
from app.modules.categories.domain.repositories import CategoryRepository


def to_result(category: Category) -> CategoryResult:
    """Map a persisted category to an application result."""
    if category.id is None:
        raise ValueError("A persisted category must have an identifier.")
    return CategoryResult(
        id=category.id,
        user_id=category.user_id,
        name=category.name,
        transaction_type=category.transaction_type,
        description=category.description,
        is_active=category.is_active,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


class GetCategory:
    """Retrieve a global or owned category."""

    def __init__(self, repository: CategoryRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, user_id: str, category_id: str) -> CategoryResult:
        """Return a visible category or hide foreign records."""
        category = await self._repository.get_by_id(category_id)
        if category is None or category.user_id not in (None, user_id):
            raise CategoryNotFoundError()
        return to_result(category)
