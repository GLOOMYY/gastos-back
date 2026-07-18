"""Unit tests for retrieving the authenticated user."""

import pytest

from app.modules.users.application.dto import CreateUserCommand
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.application.use_cases.get_user import GetUser
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    UserNotFoundError,
)
from tests.unit.application.fakes import (
    FakePasswordHasher,
    FakeUserRepository,
)


@pytest.mark.asyncio
async def test_get_user_returns_safe_active_user() -> None:
    """An active persisted user can be exposed safely."""
    repository = FakeUserRepository()
    created = await CreateUser(repository, FakePasswordHasher()).execute(
        CreateUserCommand("user@example.com", "password-1")
    )

    result = await GetUser(repository).execute(created.id)

    assert result == created


@pytest.mark.asyncio
async def test_get_user_rejects_missing_user() -> None:
    """Unknown identifiers produce a specific application failure."""
    with pytest.raises(UserNotFoundError):
        await GetUser(FakeUserRepository()).execute("missing")


@pytest.mark.asyncio
async def test_get_user_rejects_inactive_user() -> None:
    """Inactive users cannot authorize protected requests."""
    repository = FakeUserRepository()
    created = await CreateUser(repository, FakePasswordHasher()).execute(
        CreateUserCommand("user@example.com", "password-1")
    )
    user = await repository.get_by_id(created.id)
    assert user is not None
    user.deactivate()

    with pytest.raises(InactiveUserError):
        await GetUser(repository).execute(created.id)
