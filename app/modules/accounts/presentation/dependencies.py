"""FastAPI composition for financial account use cases."""

from typing import Annotated

from fastapi import Depends

from app.modules.accounts.application.use_cases.close_account import CloseAccount
from app.modules.accounts.application.use_cases.get_account import GetAccount
from app.modules.accounts.application.use_cases.list_accounts import ListAccounts
from app.modules.accounts.application.use_cases.rename_account import RenameAccount
from app.modules.accounts.application.use_cases.set_favorite_account import (
    SetFavoriteAccount,
)
from app.modules.accounts.infrastructure.favorite_store import (
    MongoFavoriteAccountStore,
)
from app.modules.accounts.infrastructure.repositories import (
    MongoAccountRepository,
)
from app.modules.users.presentation.dependencies import DatabaseDep


def get_repository(database: DatabaseDep) -> MongoAccountRepository:
    """Build the account repository."""
    return MongoAccountRepository(database)


RepositoryDep = Annotated[MongoAccountRepository, Depends(get_repository)]


def get_list(repository: RepositoryDep) -> ListAccounts:
    """Compose account listing."""
    return ListAccounts(repository)


def get_one(repository: RepositoryDep) -> GetAccount:
    """Compose account retrieval."""
    return GetAccount(repository)


def get_update(repository: RepositoryDep) -> RenameAccount:
    """Compose account metadata updates."""
    return RenameAccount(repository)


def get_close(repository: RepositoryDep) -> CloseAccount:
    """Compose account deactivation."""
    return CloseAccount(repository)


def get_set_favorite(
    database: DatabaseDep,
    repository: RepositoryDep,
) -> SetFavoriteAccount:
    """Compose atomic favorite account selection."""
    return SetFavoriteAccount(repository, MongoFavoriteAccountStore(database))


ListDep = Annotated[ListAccounts, Depends(get_list)]
GetDep = Annotated[GetAccount, Depends(get_one)]
UpdateDep = Annotated[RenameAccount, Depends(get_update)]
CloseDep = Annotated[CloseAccount, Depends(get_close)]
SetFavoriteDep = Annotated[SetFavoriteAccount, Depends(get_set_favorite)]
