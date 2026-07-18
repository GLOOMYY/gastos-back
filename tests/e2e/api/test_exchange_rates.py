"""End-to-end tests for authenticated exchange-rate endpoints."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.core.exceptions import AuthenticationRequiredError
from app.main import create_app
from app.modules.exchange_rates.application.dto import ExchangeRateQuote
from app.modules.exchange_rates.presentation.dependencies import (
    get_exchange_rate_provider,
)
from app.modules.users.application.dto import UserResult
from app.modules.users.presentation.dependencies import get_current_user


class FakeExchangeRateProvider:
    """Provide deterministic HTTP endpoint test quotes."""

    async def get_latest_rate(
        self,
        source_currency: str,
        target_currency: str,
    ) -> ExchangeRateQuote:
        """Return a fixed latest rate."""
        return ExchangeRateQuote(
            source_currency=source_currency,
            target_currency=target_currency,
            rate=Decimal("4000.25"),
            provider="fake",
            updated_at=datetime(2026, 7, 18, tzinfo=timezone.utc),
        )


def _create_test_app() -> FastAPI:
    """Build an API with authentication and provider test doubles."""
    application = create_app(Settings(_env_file=None))
    user = UserResult(
        id="507f1f77bcf86cd799439011",
        email="user@example.com",
        role="user",
        is_active=True,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    application.dependency_overrides[get_current_user] = lambda: user
    application.dependency_overrides[get_exchange_rate_provider] = (
        FakeExchangeRateProvider
    )
    return application


def _raise_authentication_required() -> None:
    """Reject an endpoint request without valid bearer credentials."""
    raise AuthenticationRequiredError()


@pytest.mark.asyncio
async def test_get_exchange_rate_endpoint() -> None:
    """The API returns a normalized current quote."""
    transport = ASGITransport(app=_create_test_app())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/exchange-rates/usd/cop")

    assert response.status_code == 200
    assert response.json()["source_currency"] == "USD"
    assert response.json()["rate"] == "4000.25"


@pytest.mark.asyncio
async def test_convert_currency_endpoint() -> None:
    """The API returns the converted amount and quote metadata."""
    transport = ASGITransport(app=_create_test_app())

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/exchange-rates/convert",
            json={
                "source_currency": "USD",
                "target_currency": "COP",
                "amount": "2.50",
            },
        )

    assert response.status_code == 200
    assert response.json()["converted_amount"] == "10000.6250"
    assert response.json()["provider"] == "fake"


@pytest.mark.asyncio
async def test_exchange_rate_endpoint_requires_authentication() -> None:
    """Currency data does not expose provider quota to anonymous clients."""
    application = _create_test_app()
    application.dependency_overrides[get_current_user] = _raise_authentication_required
    transport = ASGITransport(app=application)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/exchange-rates/USD/COP")

    assert response.status_code == 401
    assert response.json()["code"] == "authentication_required"
