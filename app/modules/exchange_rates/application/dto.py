"""Commands and results for currency conversion."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ExchangeRateQuote:
    """Normalized quote returned by an exchange-rate provider."""

    source_currency: str
    target_currency: str
    rate: Decimal
    provider: str
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class GetExchangeRateQuery:
    """Input for retrieving the latest exchange rate."""

    source_currency: str
    target_currency: str


@dataclass(frozen=True, slots=True)
class ConvertCurrencyCommand:
    """Input for converting a positive monetary amount."""

    source_currency: str
    target_currency: str
    amount: Decimal


@dataclass(frozen=True, slots=True)
class CurrencyConversionResult:
    """Converted amount and the quote used for the calculation."""

    source_currency: str
    target_currency: str
    source_amount: Decimal
    converted_amount: Decimal
    rate: Decimal
    provider: str
    updated_at: datetime
