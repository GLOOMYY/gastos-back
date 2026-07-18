"""Global country and currency catalog entities."""

from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.reference_data.domain.enums import CurrencyKind
from app.shared.domain.value_objects import Currency


@dataclass(slots=True)
class Country:
    """ISO-style country or territory and its monetary assets."""

    id: str | None
    code: str
    alpha3_code: str
    name: str
    official_name: str
    currency_codes: tuple[str, ...]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        code: str,
        alpha3_code: str,
        name: str,
        official_name: str,
        currency_codes: tuple[str, ...],
    ) -> "Country":
        """Create a validated global country catalog entry."""
        normalized_code = code.strip().upper()
        normalized_alpha3 = alpha3_code.strip().upper()
        if len(normalized_code) != 2 or not normalized_code.isalpha():
            raise ValueError("Country code must contain two letters.")
        if len(normalized_alpha3) != 3 or not normalized_alpha3.isalpha():
            raise ValueError("Country alpha-3 code must contain three letters.")
        clean_name = name.strip()
        clean_official_name = official_name.strip()
        if not clean_name or not clean_official_name:
            raise ValueError("Country names cannot be empty.")
        normalized_currencies = tuple(
            sorted({Currency.create(value).code for value in currency_codes})
        )
        now = datetime.now(UTC)
        return cls(
            id=None,
            code=normalized_code,
            alpha3_code=normalized_alpha3,
            name=clean_name,
            official_name=clean_official_name,
            currency_codes=normalized_currencies,
            is_active=True,
            created_at=now,
            updated_at=now,
        )


@dataclass(slots=True)
class CurrencyCatalogEntry:
    """Global fiat currency or cryptocurrency reference entry."""

    id: str | None
    code: str
    name: str
    symbol: str | None
    kind: CurrencyKind
    country_codes: tuple[str, ...]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        code: str,
        name: str,
        kind: CurrencyKind,
        country_codes: tuple[str, ...] = (),
        symbol: str | None = None,
    ) -> "CurrencyCatalogEntry":
        """Create a validated fiat or crypto catalog entry."""
        normalized_code = Currency.create(code).code
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Currency name cannot be empty.")
        normalized_countries = tuple(
            sorted({value.strip().upper() for value in country_codes})
        )
        if any(
            len(value) != 2 or not value.isalpha() for value in normalized_countries
        ):
            raise ValueError("Currency country codes must contain two letters.")
        clean_symbol = symbol.strip() if symbol and symbol.strip() else None
        now = datetime.now(UTC)
        return cls(
            id=None,
            code=normalized_code,
            name=clean_name,
            symbol=clean_symbol,
            kind=kind,
            country_codes=normalized_countries,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
