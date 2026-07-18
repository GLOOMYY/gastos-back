"""Composition router for API version 1."""

from fastapi import APIRouter

from app.api.v1.schemas import HealthResponse

api_v1_router = APIRouter()


@api_v1_router.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Check API availability",
)
async def health_check() -> HealthResponse:
    """Report that the HTTP application is running."""
    return HealthResponse(status="ok")
