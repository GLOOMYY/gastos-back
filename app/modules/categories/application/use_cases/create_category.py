"""Create a user-owned category."""

from app.modules.categories.application.dto import (
    CategoryResult,
    CreateCategoryCommand,
)
from app.modules.categories.application.use_cases.get_category import to_result
from app.modules.categories.domain.entities import Category
from app.modules.categories.domain.exceptions import (
    CategoryNameAlreadyExistsError,
)
from app.modules.categories.domain.repositories import CategoryRepository


class CreateCategory:
    """Create a private category."""

    def __init__(self, repository: CategoryRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, command: CreateCategoryCommand) -> CategoryResult:
        """Create a category in its owner and transaction-type scope."""
        category = Category.create(
            user_id=command.user_id,
            name=command.name,
            transaction_type=command.transaction_type,
            description=command.description,
        )
        if await self._repository.exists_name(
            command.user_id,
            category.normalized_name,
            category.transaction_type,
        ):
            raise CategoryNameAlreadyExistsError()
        return to_result(await self._repository.add(category))
