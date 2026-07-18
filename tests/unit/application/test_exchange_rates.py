"""Unit tests for exchange-rate application use cases."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.modules.exchange_rates.application.dto import (
    ConvertCurrencyCommand,
    ExchangeRateQuote,
    GetExchangeRateQuery,
)
from app.modules.exchange_rates.application.use_cases.convert_currency import (
    ConvertCurrency,
)
from app.modules.exchange_rates.application.use_cases.get_exchange_rate import (
    GetExchangeRate,
)
from app.modules.exchange_rates.domain.exceptions import (
    InvalidConversionAmountError,
)


class FakeExchangeRateProvider:
    """Return a deterministic quote without network access."""

    def __init__(self) -> None:
        """Initialize provider call tracking."""
        self.calls: list[tuple[str, str]] = []

    async def get_latest_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRateQuote:
        """Return the test COP to USD quote."""
        self.calls.append((source_currency, target_currency))
        return ExchangeRateQuote(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=Decimal("0.00025123"),
            provider="fake",
            updated_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        )


@pytest.mark.asyncio
async def test_get_exchange_rate_normalizes_currency_codes() -> None:
    """The use case validates and uppercases both currency codes."""
    provider = FakeExchangeRateProvider()
    use_case = GetExchangeRate(provider)

    result = await use_case.execute(GetExchangeRateQuery(" cop ", "usd"))

    assert result.rate == Decimal("0.00025123")
    assert provider.calls == [("COP", "USD")]


@pytest.mark.asyncio
async def test_convert_currency_preserves_decimal_precision() -> None:
    """Conversion multiplies Decimal values without float coercion."""
    provider = FakeExchangeRateProvider()
    use_case = ConvertCurrency(provider)

    result = await use_case.execute(
        ConvertCurrencyCommand(
            source_currency="COP",
            target_currency="USD",
            amount=Decimal("125000.50"),
        )
    )

    assert result.converted_amount == Decimal("31.4038756150")
    assert result.rate == Decimal("0.00025123")


@pytest.mark.asyncio
async def test_convert_currency_rejects_non_positive_amount() -> None:
    """Application validation rejects amounts that cannot be converted."""
    provider = FakeExchangeRateProvider()
    use_case = ConvertCurrency(provider)

    with pytest.raises(InvalidConversionAmountError):
        await use_case.execute(ConvertCurrencyCommand("COP", "USD", Decimal("0")))

    assert provider.calls == []
