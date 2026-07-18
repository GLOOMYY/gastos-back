"""Application results for reference catalogs."""

from dataclasses import dataclass

from app.modules.reference_data.domain.enums import CurrencyKind


@dataclass(frozen=True, slots=True)
class CountryResult:
    """Country data exposed to presentation."""

    id: str
    code: str
    alpha3_code: str
    name: str
    official_name: str
    currency_codes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CurrencyResult:
    """Fiat or crypto data exposed to presentation."""

    id: str
    code: str
    name: str
    symbol: str | None
    kind: CurrencyKind
    country_codes: tuple[str, ...]
