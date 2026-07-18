"""FastAPI composition for account type use cases."""

from typing import Annotated

from fastapi import Depends

from app.modules.account_types.application.use_cases.create_account_type import (
    CreateAccountType,
)
from app.modules.account_types.application.use_cases.deactivate_account_type import (
    DeactivateAccountType,
)
from app.modules.account_types.application.use_cases.get_account_type import (
    GetAccountType,
)
from app.modules.account_types.application.use_cases.list_account_types import (
    ListAccountTypes,
)
from app.modules.account_types.application.use_cases.update_account_type import (
    UpdateAccountType,
)
from app.modules.account_types.infrastructure.repositories import (
    MongoAccountTypeRepository,
)
from app.modules.users.presentation.dependencies import DatabaseDep


def get_repository(database: DatabaseDep) -> MongoAccountTypeRepository:
    """Build the account type repository."""
    return MongoAccountTypeRepository(database)


RepositoryDep = Annotated[MongoAccountTypeRepository, Depends(get_repository)]


def get_create(repository: RepositoryDep) -> CreateAccountType:
    """Compose account type creation."""
    return CreateAccountType(repository)


def get_list(repository: RepositoryDep) -> ListAccountTypes:
    """Compose account type listing."""
    return ListAccountTypes(repository)


def get_one(repository: RepositoryDep) -> GetAccountType:
    """Compose account type retrieval."""
    return GetAccountType(repository)


def get_update(repository: RepositoryDep) -> UpdateAccountType:
    """Compose account type updating."""
    return UpdateAccountType(repository)


def get_deactivate(repository: RepositoryDep) -> DeactivateAccountType:
    """Compose account type deactivation."""
    return DeactivateAccountType(repository)


CreateDep = Annotated[CreateAccountType, Depends(get_create)]
ListDep = Annotated[ListAccountTypes, Depends(get_list)]
GetDep = Annotated[GetAccountType, Depends(get_one)]
UpdateDep = Annotated[UpdateAccountType, Depends(get_update)]
DeactivateDep = Annotated[DeactivateAccountType, Depends(get_deactivate)]
