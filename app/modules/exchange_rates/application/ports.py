"""Application ports for external exchange-rate providers."""

from typing import Protocol

from app.modules.exchange_rates.application.dto import ExchangeRateQuote


class ExchangeRateProvider(Protocol):
    """Obtain normalized latest quotes without exposing an HTTP client."""

    async def get_latest_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRateQuote:
        """Return the latest rate for a normalized currency pair."""
        ...
