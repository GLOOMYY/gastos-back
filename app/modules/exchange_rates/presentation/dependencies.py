"""FastAPI composition for exchange-rate use cases."""

from typing import Annotated

from fastapi import Depends, Request

from app.core.exceptions import ServiceUnavailableError
from app.modules.exchange_rates.application.ports import ExchangeRateProvider
from app.modules.exchange_rates.application.use_cases.convert_currency import (
    ConvertCurrency,
)
from app.modules.exchange_rates.application.use_cases.get_exchange_rate import (
    GetExchangeRate,
)
from app.modules.exchange_rates.infrastructure.exchangerate_api import (
    ExchangeRateApiProvider,
)
from app.modules.users.presentation.dependencies import SettingsDep


def get_exchange_rate_provider(
    request: Request,
    settings: SettingsDep,
) -> ExchangeRateProvider:
    """Return the application-wide configured exchange-rate adapter."""
    provider_name = settings.exchange_rate_provider.strip().casefold()
    api_key = settings.exchange_rate_api_key
    if provider_name not in {"exchangerate_api", "exchangerate-api"}:
        raise ServiceUnavailableError("Exchange-rate configuration is unavailable.")
    if api_key is None or not api_key.get_secret_value().strip():
        raise ServiceUnavailableError("Exchange-rate configuration is unavailable.")
    existing = getattr(request.app.state, "exchange_rate_provider", None)
    if isinstance(existing, ExchangeRateApiProvider):
        return existing
    provider = ExchangeRateApiProvider(
        api_key=api_key.get_secret_value(),
        base_url=settings.exchange_rate_base_url,
        timeout_seconds=settings.exchange_rate_timeout_seconds,
        cache_ttl_seconds=settings.exchange_rate_cache_ttl_seconds,
    )
    request.app.state.exchange_rate_provider = provider
    return provider


def get_optional_exchange_rate_provider(
    request: Request,
    settings: SettingsDep,
) -> ExchangeRateProvider | None:
    """Return a provider only when market-rate settings are available."""
    try:
        return get_exchange_rate_provider(request, settings)
    except ServiceUnavailableError:
        return None


ProviderDep = Annotated[
    ExchangeRateProvider,
    Depends(get_exchange_rate_provider),
]
OptionalProviderDep = Annotated[
    ExchangeRateProvider | None,
    Depends(get_optional_exchange_rate_provider),
]


def get_exchange_rate_use_case(provider: ProviderDep) -> GetExchangeRate:
    """Compose latest exchange-rate retrieval."""
    return GetExchangeRate(provider)


def get_convert_currency_use_case(provider: ProviderDep) -> ConvertCurrency:
    """Compose currency conversion."""
    return ConvertCurrency(provider)


GetExchangeRateDep = Annotated[
    GetExchangeRate,
    Depends(get_exchange_rate_use_case),
]
ConvertCurrencyDep = Annotated[
    ConvertCurrency,
    Depends(get_convert_currency_use_case),
]
