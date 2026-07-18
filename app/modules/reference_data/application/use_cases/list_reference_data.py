"""List global countries and monetary assets."""

from app.modules.reference_data.application.dto import (
    CountryResult,
    CurrencyResult,
)
from app.modules.reference_data.domain.entities import (
    Country,
    CurrencyCatalogEntry,
)
from app.modules.reference_data.domain.enums import CurrencyKind
from app.modules.reference_data.domain.repositories import ReferenceDataRepository


def _country_result(value: Country) -> CountryResult:
    """Map a persisted country to a public result."""
    if value.id is None:
        raise ValueError("A persisted country requires an identifier.")
    return CountryResult(
        id=value.id,
        code=value.code,
        alpha3_code=value.alpha3_code,
        name=value.name,
        official_name=value.official_name,
        currency_codes=value.currency_codes,
    )


def _currency_result(value: CurrencyCatalogEntry) -> CurrencyResult:
    """Map a persisted monetary asset to a public result."""
    if value.id is None:
        raise ValueError("A persisted currency requires an identifier.")
    return CurrencyResult(
        id=value.id,
        code=value.code,
        name=value.name,
        symbol=value.symbol,
        kind=value.kind,
        country_codes=value.country_codes,
    )


class ListCountries:
    """List active country reference data."""

    def __init__(self, repository: ReferenceDataRepository) -> None:
        """Initialize with the reference repository."""
        self._repository = repository

    async def execute(self) -> list[CountryResult]:
        """Return all active countries."""
        return [
            _country_result(value) for value in await self._repository.list_countries()
        ]


class ListCurrencies:
    """List active fiat currencies and cryptocurrencies."""

    def __init__(self, repository: ReferenceDataRepository) -> None:
        """Initialize with the reference repository."""
        self._repository = repository

    async def execute(
        self,
        kind: CurrencyKind | None = None,
        country_code: str | None = None,
    ) -> list[CurrencyResult]:
        """Return monetary assets matching optional filters."""
        normalized_country = (
            country_code.strip().upper() if country_code is not None else None
        )
        return [
            _currency_result(value)
            for value in await self._repository.list_currencies(
                kind,
                normalized_country,
            )
        ]
