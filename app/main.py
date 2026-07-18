"""FastAPI application entry point."""

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Optional explicit settings, primarily for tests.

    Returns:
        The configured FastAPI application.
    """
    resolved_settings = settings or get_settings()
    application = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.debug,
    )
    application.include_router(
        api_v1_router,
        prefix=resolved_settings.api_v1_prefix,
    )

    return application


app = create_app()
