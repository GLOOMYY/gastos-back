"""Tests for the ExchangeRate-API infrastructure adapter."""

from decimal import Decimal
import json

import httpx
import pytest

from app.modules.exchange_rates.domain.exceptions import (
    ExchangeRateUnavailableError,
    UnsupportedExchangeRateCurrencyError,
)
from app.modules.exchange_rates.infrastructure.exchangerate_api import (
    ExchangeRateApiProvider,
)


def _provider(transport: httpx.AsyncBaseTransport) -> ExchangeRateApiProvider:
    """Build an adapter with deterministic test configuration."""
    return ExchangeRateApiProvider(
        api_key="test-secret",
        base_url="https://provider.test",
        timeout_seconds=1,
        cache_ttl_seconds=300,
        transport=transport,
    )


@pytest.mark.asyncio
async def test_provider_uses_bearer_auth_and_parses_decimal_rate() -> None:
    """The secret stays out of the URL and numeric precision is preserved."""
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "result": "success",
                "time_last_update_unix": 1784332800,
                "conversion_rates": {"COP": 1, "USD": 0.00025123},
            },
        )

    provider = _provider(httpx.MockTransport(handler))

    result = await provider.get_latest_rate("COP", "USD")

    assert result.rate == Decimal("0.00025123")
    assert requests[0].url == "https://provider.test/v6/latest/COP"
    assert requests[0].headers["Authorization"] == "Bearer test-secret"


@pytest.mark.asyncio
async def test_provider_caches_complete_base_currency_response() -> None:
    """Multiple target rates reuse one quota-consuming provider request."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(
            200,
            json={
                "result": "success",
                "time_last_update_unix": 1784332800,
                "conversion_rates": {"USD": 1, "COP": 4000, "EUR": 0.86},
            },
        )

    provider = _provider(httpx.MockTransport(handler))

    await provider.get_latest_rate("USD", "COP")
    await provider.get_latest_rate("USD", "EUR")

    assert call_count == 1


@pytest.mark.asyncio
async def test_provider_maps_unsupported_currency() -> None:
    """A provider currency error becomes a stable domain failure."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            200,
            json={"result": "error", "error-type": "unsupported-code"},
        )
    )

    with pytest.raises(UnsupportedExchangeRateCurrencyError):
        await _provider(transport).get_latest_rate("AAA", "USD")


@pytest.mark.asyncio
async def test_provider_hides_api_key_on_provider_failure() -> None:
    """Provider errors expose neither credentials nor raw payloads."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(
            403,
            text=json.dumps({"result": "error", "error-type": "invalid-key"}),
        )
    )

    with pytest.raises(ExchangeRateUnavailableError) as captured:
        await _provider(transport).get_latest_rate("USD", "COP")

    assert "test-secret" not in str(captured.value)
    assert "invalid-key" not in str(captured.value)
