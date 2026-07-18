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
