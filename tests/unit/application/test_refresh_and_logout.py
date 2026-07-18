"""Unit tests for refresh-token rotation and logout."""

import pytest

from app.modules.users.application.dto import (
    AuthenticateUserCommand,
    CreateUserCommand,
    LogoutUserCommand,
    RefreshSessionCommand,
)
from app.modules.users.application.use_cases.authenticate_user import (
    AuthenticateUser,
)
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.application.use_cases.logout_user import LogoutUser
from app.modules.users.application.use_cases.refresh_session import (
    RefreshSession,
)
from app.modules.users.domain.exceptions import (
    InvalidAuthenticationTokenError,
)
from tests.unit.application.fakes import (
    FakeClock,
    FakeIdGenerator,
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


async def _start_session() -> tuple[
    str,
    FakeUserRepository,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeClock,
]:
    """Register, authenticate, and return shared session test state."""
    users = FakeUserRepository()
    hasher = FakePasswordHasher()
    await CreateUser(users, hasher).execute(
        CreateUserCommand("user@example.com", "password-1")
    )
    clock = FakeClock()
    tokens = FakeTokenService(clock)
    refresh_tokens = FakeRefreshTokenRepository()
    authentication = AuthenticateUser(
        users,
        refresh_tokens,
        hasher,
        tokens,
        clock,
        FakeIdGenerator(),
    )
    pair = await authentication.execute(
        AuthenticateUserCommand("user@example.com", "password-1")
    )
    return pair.refresh_token, users, refresh_tokens, tokens, clock


@pytest.mark.asyncio
async def test_refresh_rotates_and_consumes_previous_token() -> None:
    """Successful rotation revokes the old token and stores the replacement."""
    old_token, users, repository, tokens, clock = await _start_session()
    use_case = RefreshSession(users, repository, tokens, clock)

    result = await use_case.execute(RefreshSessionCommand(old_token))

    old_record = await repository.get_by_hash(tokens.hash_token(old_token))
    new_record = await repository.get_by_hash(tokens.hash_token(result.refresh_token))
    assert old_record is not None
    assert new_record is not None
    assert old_record.revoked_at == clock.now()
    assert old_record.replaced_by_id == new_record.id
    assert new_record.family_id == old_record.family_id


@pytest.mark.asyncio
async def test_refresh_reuse_revokes_token_family() -> None:
    """Reusing a rotated token invalidates its complete family."""
    old_token, users, repository, tokens, clock = await _start_session()
    use_case = RefreshSession(users, repository, tokens, clock)
    result = await use_case.execute(RefreshSessionCommand(old_token))

    with pytest.raises(InvalidAuthenticationTokenError):
        await use_case.execute(RefreshSessionCommand(old_token))

    new_record = await repository.get_by_hash(tokens.hash_token(result.refresh_token))
    assert new_record is not None
    assert new_record.revoked_at == clock.now()


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token_idempotently() -> None:
    """Logout revokes a token and remains safe to repeat."""
    token, _, repository, tokens, clock = await _start_session()
    use_case = LogoutUser(repository, tokens, clock)

    await use_case.execute(LogoutUserCommand(token))
    await use_case.execute(LogoutUserCommand(token))

    record = await repository.get_by_hash(tokens.hash_token(token))
    assert record is not None
    assert record.revoked_at == clock.now()
