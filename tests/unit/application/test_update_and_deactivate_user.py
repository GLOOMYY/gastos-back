"""Unit tests for authenticated user update and soft deletion."""

import pytest

from app.modules.users.application.dto import (
    AuthenticateUserCommand,
    CreateUserCommand,
    DeactivateUserCommand,
    UpdateUserCommand,
)
from app.modules.users.application.use_cases.authenticate_user import (
    AuthenticateUser,
)
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.application.use_cases.deactivate_user import (
    DeactivateUser,
)
from app.modules.users.application.use_cases.update_user import UpdateUser
from app.modules.users.domain.exceptions import (
    InvalidFavoriteCurrencyError,
    InvalidUserCountryError,
    NoUserChangesError,
    UserAlreadyExistsError,
)
from tests.unit.application.fakes import (
    FakeClock,
    FakeIdGenerator,
    FakePasswordHasher,
    FakeRefreshTokenRepository,
    FakeTokenService,
    FakeUserRepository,
)


class FakeReferenceData:
    """Validate a small deterministic profile catalog."""

    async def country_exists(self, code: str) -> bool:
        """Accept Colombia only."""
        return code == "CO"

    async def currency_exists(self, code: str) -> bool:
        """Accept COP and one principal cryptocurrency."""
        return code in {"COP", "BTC"}


async def _build_user_crud() -> tuple[
    str,
    FakeUserRepository,
    FakeRefreshTokenRepository,
    FakePasswordHasher,
    FakeClock,
]:
    """Build a registered user and CRUD test dependencies."""
    users = FakeUserRepository()
    hasher = FakePasswordHasher()
    created = await CreateUser(users, hasher).execute(
        CreateUserCommand("user@example.com", "password-1")
    )
    return (
        created.id,
        users,
        FakeRefreshTokenRepository(),
        hasher,
        FakeClock(),
    )


@pytest.mark.asyncio
async def test_update_user_changes_email() -> None:
    """An authenticated user may change to an available email."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()
    use_case = UpdateUser(users, refresh_tokens, hasher, clock)

    result = await use_case.execute(
        UpdateUserCommand(
            user_id=user_id,
            email=" New@Example.com ",
        )
    )

    assert result.email == "New@Example.com"
    assert await users.get_by_normalized_email("new@example.com") is not None


@pytest.mark.asyncio
async def test_update_user_rejects_duplicate_email() -> None:
    """A user cannot adopt another user's normalized email."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()
    await CreateUser(users, hasher).execute(
        CreateUserCommand("other@example.com", "password-2")
    )
    use_case = UpdateUser(users, refresh_tokens, hasher, clock)

    with pytest.raises(UserAlreadyExistsError):
        await use_case.execute(
            UpdateUserCommand(user_id=user_id, email="OTHER@example.com")
        )


@pytest.mark.asyncio
async def test_password_update_revokes_all_refresh_tokens() -> None:
    """Changing a password invalidates every renewable session."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()
    tokens = FakeTokenService(clock)
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

    await UpdateUser(users, refresh_tokens, hasher, clock).execute(
        UpdateUserCommand(user_id=user_id, password="new-password")
    )

    record = await refresh_tokens.get_by_hash(tokens.hash_token(pair.refresh_token))
    user = await users.get_by_id(user_id)
    assert record is not None
    assert record.revoked_at == clock.now()
    assert user is not None
    assert user.password_hash == "hashed:new-password"


@pytest.mark.asyncio
async def test_update_user_rejects_empty_changes() -> None:
    """Application callers must request at least one supported change."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()

    with pytest.raises(NoUserChangesError):
        await UpdateUser(users, refresh_tokens, hasher, clock).execute(
            UpdateUserCommand(user_id=user_id)
        )


@pytest.mark.asyncio
async def test_update_user_changes_profile_name() -> None:
    """The authenticated user may set a normalized display name."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()

    result = await UpdateUser(users, refresh_tokens, hasher, clock).execute(
        UpdateUserCommand(user_id=user_id, name="  Ana   Gómez  ")
    )

    assert result.name == "Ana Gómez"


@pytest.mark.asyncio
async def test_update_user_sets_country_and_favorite_currency() -> None:
    """Profile preferences are normalized and validated by the catalog."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()

    result = await UpdateUser(
        users,
        refresh_tokens,
        hasher,
        clock,
        FakeReferenceData(),
    ).execute(
        UpdateUserCommand(
            user_id=user_id,
            favorite_currency="btc",
            country_code="co",
        )
    )

    assert result.favorite_currency == "BTC"
    assert result.country_code == "CO"


@pytest.mark.asyncio
async def test_update_user_rejects_unknown_profile_references() -> None:
    """Unknown countries and currencies cannot enter the profile."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()
    use_case = UpdateUser(
        users,
        refresh_tokens,
        hasher,
        clock,
        FakeReferenceData(),
    )

    with pytest.raises(InvalidFavoriteCurrencyError):
        await use_case.execute(
            UpdateUserCommand(user_id=user_id, favorite_currency="ETH")
        )
    with pytest.raises(InvalidUserCountryError):
        await use_case.execute(UpdateUserCommand(user_id=user_id, country_code="US"))


@pytest.mark.asyncio
async def test_deactivate_user_soft_deletes_and_revokes_sessions() -> None:
    """Soft deletion preserves the user while disabling renewable sessions."""
    user_id, users, refresh_tokens, hasher, clock = await _build_user_crud()
    tokens = FakeTokenService(clock)
    pair = await AuthenticateUser(
        users,
        refresh_tokens,
        hasher,
        tokens,
        clock,
        FakeIdGenerator(),
    ).execute(AuthenticateUserCommand("user@example.com", "password-1"))

    await DeactivateUser(users, refresh_tokens, clock).execute(
        DeactivateUserCommand(user_id)
    )

    user = await users.get_by_id(user_id)
    record = await refresh_tokens.get_by_hash(tokens.hash_token(pair.refresh_token))
    assert user is not None
    assert user.is_active is False
    assert record is not None
    assert record.revoked_at == clock.now()
