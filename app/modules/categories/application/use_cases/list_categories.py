"""List categories visible to a user."""

from app.modules.categories.application.dto import CategoryResult
from app.modules.categories.application.use_cases.get_category import to_result
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.domain.repositories import CategoryRepository


class ListCategories:
    """List active global and private categories."""

    def __init__(self, repository: CategoryRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        transaction_type: CategoryTransactionType | None = None,
    ) -> list[CategoryResult]:
        """Return available categories with an optional type filter."""
        values = await self._repository.list_available(user_id, transaction_type)
        return [to_result(value) for value in values]
