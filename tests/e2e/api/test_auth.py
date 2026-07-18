"""End-to-end HTTP tests for the complete authentication flow."""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app
from app.modules.users.presentation.dependencies import (
    get_clock,
    get_id_generator,
    get_password_hasher,
    get_refresh_token_repository,
    get_token_service,
    get_user_repository,
)
from tests.unit.application.fakes import (
    FakeClock,
    FakeIdGenerator,
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


def _create_test_app() -> FastAPI:
    """Build an application using in-memory authentication adapters."""
    application = create_app(Settings(_env_file=None))
    clock = FakeClock()
    users = FakeUserRepository()
    refresh_tokens = FakeRefreshTokenRepository()
    hasher = FakePasswordHasher()
    tokens = FakeTokenService(clock)
    id_generator = FakeIdGenerator()
    application.dependency_overrides[get_user_repository] = lambda: users
    application.dependency_overrides[get_refresh_token_repository] = lambda: (
        refresh_tokens
    )
    application.dependency_overrides[get_password_hasher] = lambda: hasher
    application.dependency_overrides[get_token_service] = lambda: tokens
    application.dependency_overrides[get_clock] = lambda: clock
    application.dependency_overrides[get_id_generator] = lambda: id_generator
    return application


@pytest.mark.asyncio
async def test_complete_authentication_flow() -> None:
    """Register, login, authorize, rotate, detect reuse, and logout."""
    application = _create_test_app()
    transport = ASGITransport(app=application)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "strong-password",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "USER@example.com",
                "password": "strong-password",
            },
        )

        assert register_response.status_code == 201
        assert register_response.json()["email"] == "user@example.com"
        assert "password_hash" not in register_response.json()
        assert login_response.status_code == 200

        first_pair = login_response.json()
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {first_pair['access_token']}"},
        )
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_pair["refresh_token"]},
        )

        assert me_response.status_code == 200
        assert me_response.json()["id"] == register_response.json()["id"]
        assert refresh_response.status_code == 200
        second_pair = refresh_response.json()
        assert second_pair["refresh_token"] != first_pair["refresh_token"]

        reuse_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": first_pair["refresh_token"]},
        )
        logout_response = await client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": second_pair["refresh_token"]},
        )

    assert reuse_response.status_code == 401
    assert reuse_response.json()["code"] == "invalid_authentication_token"
    assert logout_response.status_code == 204
    assert logout_response.content == b""


@pytest.mark.asyncio
async def test_login_failure_uses_standard_error_envelope() -> None:
    """Invalid credentials never reveal which credential was rejected."""
    application = _create_test_app()
    transport = ASGITransport(app=application)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "missing@example.com",
                "password": "wrong-password",
            },
        )

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert response.json()["code"] == "invalid_credentials"
    assert response.json()["details"] is None
    assert response.json()["request_id"]


@pytest.mark.asyncio
async def test_unknown_route_uses_standard_error_envelope() -> None:
    """Framework-generated 404 responses follow the shared contract."""
    application = _create_test_app()
    transport = ASGITransport(app=application)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/v1/unknown")

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert response.json()["details"] is None
    assert response.json()["request_id"]


@pytest.mark.asyncio
async def test_authenticated_user_crud_flow() -> None:
    """The current user can read, update, and soft-delete itself."""
    application = _create_test_app()
    transport = ASGITransport(app=application)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "strong-password",
            },
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "strong-password",
            },
        )
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        get_response = await client.get("/api/v1/users/me", headers=headers)
        update_response = await client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={
                "email": "updated@example.com",
                "password": "updated-password",
            },
        )
        old_refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )
        delete_response = await client.delete(
            "/api/v1/users/me",
            headers=headers,
        )
        after_delete_response = await client.get(
            "/api/v1/users/me",
            headers=headers,
        )

    assert get_response.status_code == 200
    assert get_response.json()["email"] == "user@example.com"
    assert update_response.status_code == 200
    assert update_response.json()["email"] == "updated@example.com"
    assert old_refresh_response.status_code == 401
    assert delete_response.status_code == 204
    assert after_delete_response.status_code == 403
