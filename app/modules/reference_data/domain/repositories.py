"""Repository contracts for global reference catalogs."""

from typing import Protocol

from app.modules.reference_data.domain.entities import (
    Country,
    CurrencyCatalogEntry,
)
from app.modules.reference_data.domain.enums import CurrencyKind


class ReferenceDataRepository(Protocol):
    """Read and seed global countries and currencies."""

    async def list_countries(self) -> list[Country]:
        """List active countries ordered by name."""
        ...

    async def list_currencies(
        self,
        kind: CurrencyKind | None = None,
        country_code: str | None = None,
    ) -> list[CurrencyCatalogEntry]:
        """List active currencies with optional catalog filters."""
        ...

    async def country_exists(self, code: str) -> bool:
        """Return whether an active country code exists."""
        ...

    async def currency_exists(self, code: str) -> bool:
        """Return whether an active currency or crypto code exists."""
        ...

    async def upsert_countries(self, values: list[Country]) -> int:
        """Idempotently create or update country reference entries."""
        ...

    async def upsert_currencies(
        self,
        values: list[CurrencyCatalogEntry],
    ) -> int:
        """Idempotently create or update currency reference entries."""
        ...
