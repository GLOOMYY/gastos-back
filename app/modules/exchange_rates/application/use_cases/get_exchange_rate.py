"""Retrieve a current exchange-rate quote."""

from app.modules.exchange_rates.application.dto import (
    ExchangeRateQuote,
    GetExchangeRateQuery,
)
from app.modules.exchange_rates.application.ports import ExchangeRateProvider
from app.shared.domain.value_objects import Currency


class GetExchangeRate:
    """Retrieve the latest normalized quote from the configured provider."""

    def __init__(self, provider: ExchangeRateProvider) -> None:
        """Initialize the use case with an external provider port."""
        self._provider = provider

    async def execute(self, query: GetExchangeRateQuery) -> ExchangeRateQuote:
        """Validate currency codes and retrieve their latest rate."""
        source = Currency.create(query.source_currency)
        target = Currency.create(query.target_currency)
        return await self._provider.get_latest_rate(source.code, target.code)
