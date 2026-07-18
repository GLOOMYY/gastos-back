"""ExchangeRate-API HTTP adapter with safe authentication and caching."""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
from time import monotonic
from types import MappingProxyType
from typing import cast

import httpx

from app.modules.exchange_rates.application.dto import ExchangeRateQuote
from app.modules.exchange_rates.domain.exceptions import (
    ExchangeRateUnavailableError,
    UnsupportedExchangeRateCurrencyError,
)


@dataclass(frozen=True, slots=True)
class _LatestRates:
    """Validated provider response cached for one base currency."""

    rates: MappingProxyType[str, Decimal]
    updated_at: datetime
    expires_at: float


class ExchangeRateApiProvider:
    """Retrieve latest rates from ExchangeRate-API's standard endpoint."""

    name = "exchangerate-api"

    def __init__(
        self,
        api_key: str,
        base_url: str,
        timeout_seconds: float,
        cache_ttl_seconds: int,
        transport: httpx.AsyncBaseTransport | None = None,
        retry_attempts: int = 2,
    ) -> None:
        """Initialize the provider without exposing its secret in the URL."""
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._cache_ttl_seconds = cache_ttl_seconds
        self._transport = transport
        self._retry_attempts = max(1, retry_attempts)
        self._cache: dict[str, _LatestRates] = {}
        self._lock = asyncio.Lock()

    async def get_latest_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRateQuote:
        """Return a cached or freshly retrieved quote for a currency pair."""
        latest = await self._get_latest_rates(source_currency)
        rate = latest.rates.get(target_currency)
        if rate is None:
            raise UnsupportedExchangeRateCurrencyError()
        return ExchangeRateQuote(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=rate,
            provider=self.name,
            updated_at=latest.updated_at,
        )

    async def _get_latest_rates(self, source_currency: str) -> _LatestRates:
        """Cache complete standard responses to minimize quota usage."""
        cached = self._cache.get(source_currency)
        if cached is not None and cached.expires_at > monotonic():
            return cached
        async with self._lock:
            cached = self._cache.get(source_currency)
            if cached is not None and cached.expires_at > monotonic():
                return cached
            latest = await self._request_latest(source_currency)
            self._cache[source_currency] = latest
            return latest

    async def _request_latest(self, source_currency: str) -> _LatestRates:
        """Call the provider with controlled retries for transient failures."""
        for attempt in range(self._retry_attempts):
            try:
                async with httpx.AsyncClient(
                    base_url=self._base_url,
                    timeout=self._timeout_seconds,
                    transport=self._transport,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                ) as client:
                    response = await client.get(f"/v6/latest/{source_currency}")
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        "Exchange-rate provider server error.",
                        request=response.request,
                        response=response,
                    )
                return self._parse_response(response)
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError):
                if attempt + 1 == self._retry_attempts:
                    raise ExchangeRateUnavailableError() from None
                await asyncio.sleep(0.1 * (attempt + 1))
        raise ExchangeRateUnavailableError()

    def _parse_response(self, response: httpx.Response) -> _LatestRates:
        """Validate and normalize the provider response."""
        try:
            raw_payload: object = json.loads(response.text, parse_float=Decimal)
        except (json.JSONDecodeError, InvalidOperation):
            raise ExchangeRateUnavailableError() from None
        if not isinstance(raw_payload, dict):
            raise ExchangeRateUnavailableError()
        payload = cast(dict[str, object], raw_payload)
        if payload.get("result") == "error":
            if payload.get("error-type") == "unsupported-code":
                raise UnsupportedExchangeRateCurrencyError()
            raise ExchangeRateUnavailableError()
        if response.is_error or payload.get("result") != "success":
            raise ExchangeRateUnavailableError()

        raw_rates = payload.get("conversion_rates")
        raw_timestamp = payload.get("time_last_update_unix")
        if (
            not isinstance(raw_rates, dict)
            or not isinstance(raw_timestamp, int)
            or isinstance(raw_timestamp, bool)
        ):
            raise ExchangeRateUnavailableError()
        rates: dict[str, Decimal] = {}
        for code, value in cast(dict[object, object], raw_rates).items():
            if not isinstance(code, str):
                raise ExchangeRateUnavailableError()
            try:
                rate = Decimal(str(value))
            except InvalidOperation:
                raise ExchangeRateUnavailableError() from None
            if rate <= 0:
                raise ExchangeRateUnavailableError()
            rates[code] = rate
        try:
            updated_at = datetime.fromtimestamp(raw_timestamp, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            raise ExchangeRateUnavailableError() from None
        return _LatestRates(
            rates=MappingProxyType(rates),
            updated_at=updated_at,
            expires_at=monotonic() + self._cache_ttl_seconds,
        )
