"""Composition router for API version 1."""

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse
from app.modules.account_types.presentation.router import (
    router as account_types_router,
)
from app.modules.accounts.presentation.router import router as accounts_router
from app.modules.categories.presentation.router import router as categories_router
from app.modules.transactions.presentation.router import (
    router as transactions_router,
)
from app.modules.users.presentation.router import router as auth_router
from app.modules.users.presentation.user_router import router as users_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(account_types_router)
api_v1_router.include_router(categories_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(transactions_router)


@api_v1_router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API availability",
)
async def health_check() -> HealthResponse:
    """Report that the HTTP application is running."""
    return HealthResponse(status="ok")
