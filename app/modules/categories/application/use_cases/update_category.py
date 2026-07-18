"""Update a user-owned category."""

from app.modules.categories.application.dto import (
    CategoryResult,
    UpdateCategoryCommand,
)
from app.modules.categories.application.use_cases.get_category import to_result
from app.modules.categories.domain.exceptions import (
    CategoryAccessDeniedError,
    CategoryNameAlreadyExistsError,
    CategoryNotFoundError,
)
from app.modules.categories.domain.repositories import CategoryRepository


class UpdateCategory:
    """Update an owned category."""

    def __init__(self, repository: CategoryRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(self, command: UpdateCategoryCommand) -> CategoryResult:
        """Update the category after authorization and uniqueness checks."""
        category = await self._repository.get_by_id(command.category_id)
        if category is None:
            raise CategoryNotFoundError()
        if category.user_id != command.user_id:
            raise CategoryAccessDeniedError()
        category.update_details(
            command.name,
            command.transaction_type,
            command.description,
        )
        if await self._repository.exists_name(
            command.user_id,
            category.normalized_name,
            category.transaction_type,
            excluding_id=command.category_id,
        ):
            raise CategoryNameAlreadyExistsError()
        return to_result(await self._repository.update(category))
