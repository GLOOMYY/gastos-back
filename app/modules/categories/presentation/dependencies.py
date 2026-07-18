"""FastAPI composition for category use cases."""

from typing import Annotated

from fastapi import Depends

from app.modules.categories.application.use_cases.create_category import (
    CreateCategory,
)
from app.modules.categories.application.use_cases.deactivate_category import (
    DeactivateCategory,
)
from app.modules.categories.application.use_cases.get_category import GetCategory
from app.modules.categories.application.use_cases.list_categories import (
    ListCategories,
)
from app.modules.categories.application.use_cases.update_category import (
    UpdateCategory,
)
from app.modules.categories.infrastructure.repositories import (
    MongoCategoryRepository,
)
from app.modules.users.presentation.dependencies import DatabaseDep


def get_repository(database: DatabaseDep) -> MongoCategoryRepository:
    """Build the category repository."""
    return MongoCategoryRepository(database)


RepositoryDep = Annotated[MongoCategoryRepository, Depends(get_repository)]


def get_create(repository: RepositoryDep) -> CreateCategory:
    """Compose category creation."""
    return CreateCategory(repository)


def get_list(repository: RepositoryDep) -> ListCategories:
    """Compose category listing."""
    return ListCategories(repository)


def get_one(repository: RepositoryDep) -> GetCategory:
    """Compose category retrieval."""
    return GetCategory(repository)


def get_update(repository: RepositoryDep) -> UpdateCategory:
    """Compose category updating."""
    return UpdateCategory(repository)


def get_deactivate(repository: RepositoryDep) -> DeactivateCategory:
    """Compose category deactivation."""
    return DeactivateCategory(repository)


CreateDep = Annotated[CreateCategory, Depends(get_create)]
ListDep = Annotated[ListCategories, Depends(get_list)]
GetDep = Annotated[GetCategory, Depends(get_one)]
UpdateDep = Annotated[UpdateCategory, Depends(get_update)]
DeactivateDep = Annotated[DeactivateCategory, Depends(get_deactivate)]
