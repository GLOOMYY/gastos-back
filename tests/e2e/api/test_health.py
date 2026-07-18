"""End-to-end tests for the API health endpoint."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app


@pytest.mark.asyncio
async def test_health_endpoint_reports_api_is_available() -> None:
    """The versioned health endpoint returns the explicit response schema."""
    application = create_app(Settings(_env_file=None))
    transport = ASGITransport(app=application)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_configured_frontend_origin_receives_cors_headers() -> None:
    """Allow browser preflight only for explicitly configured origins."""
    application = create_app(
        Settings(
            _env_file=None,
            cors_allowed_origins="https://app.example.com",
        )
    )
    transport = ASGITransport(app=application)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.options(
            "/api/v1/health",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == (
        "https://app.example.com"
    )


def test_production_configuration_requires_runtime_secrets() -> None:
    """Reject a production process that would start without persistence."""
    settings = Settings(_env_file=None, environment="production")

    with pytest.raises(RuntimeError, match="MONGODB_URI"):
        settings.validate_production_configuration()


def test_production_configuration_rejects_wildcard_cors() -> None:
    """Do not permit credentialed browser access from every origin."""
    settings = Settings(
        _env_file=None,
        environment="production",
        mongodb_uri="mongodb://example.invalid",
        mongodb_database="gastos",
        jwt_secret_key="x" * 32,
        cors_allowed_origins="*",
    )

    with pytest.raises(RuntimeError, match="Wildcard CORS"):
        settings.validate_production_configuration()
