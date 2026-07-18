"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RequestIdMiddleware
from app.shared.infrastructure.mongodb.client import MongoDatabase
from app.shared.infrastructure.mongodb.indexes import create_indexes
from app.shared.infrastructure.mongodb.schema import (
    ensure_auth_collection_schemas,
)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build and configure the FastAPI application.

    Args:
        settings: Optional explicit settings, primarily for tests.

    Returns:
        The configured FastAPI application.
    """
    resolved_settings = settings or get_settings()
    mongo_database = MongoDatabase()

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        """Connect configured infrastructure for the application lifetime."""
        try:
            mongodb_uri = resolved_settings.mongodb_uri
            mongodb_database = resolved_settings.mongodb_database
            if mongodb_uri is not None and mongodb_database:
                await mongo_database.connect(
                    mongodb_uri.get_secret_value(),
                    mongodb_database,
                )
                database = mongo_database.get_database()
                await ensure_auth_collection_schemas(database)
                await create_indexes(database)
            yield
        finally:
            await mongo_database.disconnect()

    application = FastAPI(
        title=resolved_settings.app_name,
        debug=resolved_settings.debug,
        lifespan=lifespan,
    )
    application.state.settings = resolved_settings
    application.state.mongo_database = mongo_database
    application.add_middleware(RequestIdMiddleware)
    application.include_router(
        api_v1_router,
        prefix=resolved_settings.api_v1_prefix,
    )
    register_exception_handlers(application)

    return application


app = create_app()
