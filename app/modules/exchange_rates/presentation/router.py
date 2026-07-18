"""Authenticated HTTP routes for exchange rates."""

from fastapi import APIRouter

from app.modules.exchange_rates.application.dto import (
    ConvertCurrencyCommand,
    GetExchangeRateQuery,
)
from app.modules.exchange_rates.presentation.dependencies import (
    ConvertCurrencyDep,
    GetExchangeRateDep,
)
from app.modules.exchange_rates.presentation.schemas import (
    ConvertCurrencyRequest,
    CurrencyConversionResponse,
    ExchangeRateResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/exchange-rates", tags=["Exchange rates"])


@router.post("/convert", response_model=CurrencyConversionResponse)
async def convert_currency(
    request: ConvertCurrencyRequest,
    current_user: CurrentUserDep,
    use_case: ConvertCurrencyDep,
) -> CurrencyConversionResponse:
    """Convert an amount using the latest rate for an authenticated user."""
    _ = current_user.id
    result = await use_case.execute(
        ConvertCurrencyCommand(
            source_currency=request.source_currency,
            target_currency=request.target_currency,
            amount=request.amount,
        )
    )
    return CurrencyConversionResponse.model_validate(result)


@router.get(
    "/{source_currency}/{target_currency}",
    response_model=ExchangeRateResponse,
)
async def get_exchange_rate(
    source_currency: str,
    target_currency: str,
    current_user: CurrentUserDep,
    use_case: GetExchangeRateDep,
) -> ExchangeRateResponse:
    """Return the latest rate for an authenticated user."""
    _ = current_user.id
    result = await use_case.execute(
        GetExchangeRateQuery(
            source_currency=source_currency,
            target_currency=target_currency,
        )
    )
    return ExchangeRateResponse.model_validate(result)
