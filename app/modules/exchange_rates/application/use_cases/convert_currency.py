"""Convert an amount using the latest available exchange rate."""

from app.modules.exchange_rates.application.dto import (
    ConvertCurrencyCommand,
    CurrencyConversionResult,
)
from app.modules.exchange_rates.application.ports import ExchangeRateProvider
from app.modules.exchange_rates.domain.exceptions import (
    InvalidConversionAmountError,
)
from app.shared.domain.value_objects import Currency


class ConvertCurrency:
    """Convert a positive amount while preserving decimal precision."""

    def __init__(self, provider: ExchangeRateProvider) -> None:
        """Initialize the use case with an external provider port."""
        self._provider = provider

    async def execute(
        self,
        command: ConvertCurrencyCommand,
    ) -> CurrencyConversionResult:
        """Return the conversion and the exact quote used for it."""
        if command.amount <= 0:
            raise InvalidConversionAmountError()
        source = Currency.create(command.source_currency)
        target = Currency.create(command.target_currency)
        quote = await self._provider.get_latest_rate(source.code, target.code)
        return CurrencyConversionResult(
            source_currency=quote.source_currency,
            target_currency=quote.target_currency,
            source_amount=command.amount,
            converted_amount=command.amount * quote.rate,
            rate=quote.rate,
            provider=quote.provider,
            updated_at=quote.updated_at,
        )
