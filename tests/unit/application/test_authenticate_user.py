"""Unit tests for email and password authentication."""

import pytest

from app.modules.users.application.dto import (
    AuthenticateUserCommand,
    CreateUserCommand,
)
from app.modules.users.application.use_cases.authenticate_user import (
    AuthenticateUser,
)
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
)
from tests.unit.application.fakes import (
    FakeClock,
    FakeIdGenerator,
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


async def _build_authentication() -> tuple[
    AuthenticateUser,
    FakeUserRepository,
    FakeRefreshTokenRepository,
    FakeTokenService,
]:
    """Create a registered user and authentication test doubles."""
    users = FakeUserRepository()
    hasher = FakePasswordHasher()
    await CreateUser(users, hasher).execute(
        CreateUserCommand("user@example.com", "password-1")
    )
    clock = FakeClock()
    tokens = FakeTokenService(clock)
    refresh_tokens = FakeRefreshTokenRepository()
    use_case = AuthenticateUser(
        users,
        refresh_tokens,
        hasher,
        tokens,
        clock,
        FakeIdGenerator(),
    )
    return use_case, users, refresh_tokens, tokens


@pytest.mark.asyncio
async def test_authenticate_user_issues_and_persists_token_pair() -> None:
    """Valid credentials start a refresh-token family."""
    use_case, _, refresh_tokens, tokens = await _build_authentication()

    result = await use_case.execute(
        AuthenticateUserCommand("USER@example.com", "password-1")
    )

    assert result.access_token.startswith("access-")
    assert result.refresh_token.startswith("refresh-")
    token_hash = tokens.hash_token(result.refresh_token)
    record = await refresh_tokens.get_by_hash(token_hash)
    assert record is not None
    assert record.user_id == "user-1"
    assert record.family_id == "family-1"


@pytest.mark.asyncio
async def test_authenticate_user_rejects_unknown_email() -> None:
    """Unknown email and wrong password use the same public error."""
    use_case, _, _, _ = await _build_authentication()

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            AuthenticateUserCommand("missing@example.com", "password-1")
        )


@pytest.mark.asyncio
async def test_authenticate_user_rejects_wrong_password() -> None:
    """A password mismatch cannot start a session."""
    use_case, _, _, _ = await _build_authentication()

    with pytest.raises(InvalidCredentialsError):
        await use_case.execute(
            AuthenticateUserCommand("user@example.com", "wrong-password")
        )


@pytest.mark.asyncio
async def test_authenticate_user_rejects_inactive_user() -> None:
    """Inactive users cannot start new sessions."""
    use_case, users, _, _ = await _build_authentication()
    user = await users.get_by_id("user-1")
    assert user is not None
    user.deactivate()

    with pytest.raises(InactiveUserError):
        await use_case.execute(
            AuthenticateUserCommand("user@example.com", "password-1")
        )
