"""Authenticated read-only routes for global reference catalogs."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.modules.reference_data.domain.enums import CurrencyKind
from app.modules.reference_data.presentation.dependencies import (
    ListCountriesDep,
    ListCurrenciesDep,
)
from app.modules.reference_data.presentation.schemas import (
    CountryResponse,
    CurrencyResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(tags=["Reference data"])


@router.get("/countries", response_model=list[CountryResponse])
async def list_countries(
    current_user: CurrentUserDep,
    use_case: ListCountriesDep,
) -> list[CountryResponse]:
    """List all active countries and territories."""
    _ = current_user.id
    return [CountryResponse.model_validate(value) for value in await use_case.execute()]


@router.get("/currencies", response_model=list[CurrencyResponse])
async def list_currencies(
    current_user: CurrentUserDep,
    use_case: ListCurrenciesDep,
    kind: CurrencyKind | None = None,
    country_code: Annotated[
        str | None,
        Query(min_length=2, max_length=2, pattern=r"^[A-Za-z]{2}$"),
    ] = None,
) -> list[CurrencyResponse]:
    """List fiat and crypto assets with optional filters."""
    _ = current_user.id
    return [
        CurrencyResponse.model_validate(value)
        for value in await use_case.execute(kind, country_code)
    ]
