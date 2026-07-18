"""Unit tests for user registration."""

import pytest

from app.modules.users.application.dto import CreateUserCommand
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.domain.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
)
from tests.unit.application.fakes import (
    FakePasswordHasher,
    FakeUserRepository,
)


@pytest.mark.asyncio
async def test_create_user_hashes_password_and_returns_safe_result() -> None:
    """Registration persists a normalized user without exposing its hash."""
    repository = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = CreateUser(repository, hasher)

    result = await use_case.execute(
        CreateUserCommand(
            email=" User@Example.com ",
            password="strong-password",
        )
    )

    assert result.id == "user-1"
    assert result.email == "User@Example.com"
    assert result.role == "user"
    assert hasher.hash_calls == 1
    stored_user = await repository.get_by_id(result.id)
    assert stored_user is not None
    assert stored_user.password_hash == "hashed:strong-password"


@pytest.mark.asyncio
async def test_create_user_rejects_duplicate_normalized_email() -> None:
    """Email uniqueness is case-insensitive."""
    repository = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = CreateUser(repository, hasher)
    await use_case.execute(CreateUserCommand("user@example.com", "password-1"))

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(CreateUserCommand("USER@example.com", "password-2"))


@pytest.mark.asyncio
async def test_create_user_rejects_short_password() -> None:
    """Password policy is enforced before hashing or persistence."""
    hasher = FakePasswordHasher()
    use_case = CreateUser(FakeUserRepository(), hasher)

    with pytest.raises(InvalidPasswordError):
        await use_case.execute(CreateUserCommand("user@example.com", "short"))

    assert hasher.hash_calls == 0
