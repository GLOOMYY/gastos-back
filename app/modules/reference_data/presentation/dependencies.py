"""FastAPI composition for reference catalog queries."""

from typing import Annotated

from fastapi import Depends

from app.modules.reference_data.application.use_cases.list_reference_data import (
    ListCountries,
    ListCurrencies,
)
from app.modules.reference_data.infrastructure.repositories import (
    MongoReferenceDataRepository,
)
from app.modules.users.presentation.dependencies import DatabaseDep


def get_repository(database: DatabaseDep) -> MongoReferenceDataRepository:
    """Build the global reference data repository."""
    return MongoReferenceDataRepository(database)


RepositoryDep = Annotated[
    MongoReferenceDataRepository,
    Depends(get_repository),
]


def get_list_countries(repository: RepositoryDep) -> ListCountries:
    """Compose country listing."""
    return ListCountries(repository)


def get_list_currencies(repository: RepositoryDep) -> ListCurrencies:
    """Compose currency listing."""
    return ListCurrencies(repository)


ListCountriesDep = Annotated[ListCountries, Depends(get_list_countries)]
ListCurrenciesDep = Annotated[ListCurrencies, Depends(get_list_currencies)]
