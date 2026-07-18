"""Composition router for API version 1."""

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse
from app.modules.users.presentation.router import router as auth_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)


@api_v1_router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API availability",
)
async def health_check() -> HealthResponse:
    """Report that the HTTP application is running."""
    return HealthResponse(status="ok")
