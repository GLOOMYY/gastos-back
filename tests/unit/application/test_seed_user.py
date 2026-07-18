"""Unit tests for the idempotent initial-user seed."""

import pytest

from app.modules.users.application.use_cases.create_user import CreateUser
from app.core.config import Settings
from scripts.seed_user import (
    SeedOutcome,
    create_initial_user,
    seed_initial_user,
)
from tests.unit.application.fakes import (
    FakePasswordHasher,
    FakeUserRepository,
)


@pytest.mark.asyncio
async def test_initial_user_seed_is_idempotent() -> None:
    """Running the seed twice creates only one user and keeps its password."""
    repository = FakeUserRepository()
    hasher = FakePasswordHasher()
    use_case = CreateUser(repository, hasher)

    first_outcome = await create_initial_user(
        use_case,
        "initial@example.com",
        "strong-password",
    )
    second_outcome = await create_initial_user(
        use_case,
        "INITIAL@example.com",
        "different-password",
    )

    assert first_outcome is SeedOutcome.CREATED
    assert second_outcome is SeedOutcome.ALREADY_EXISTS
    assert len(repository.users) == 1
    assert hasher.hash_calls == 1


@pytest.mark.asyncio
async def test_initial_user_seed_requires_explicit_configuration() -> None:
    """The seed fails before connecting when required settings are absent."""
    settings = Settings(_env_file=None)

    with pytest.raises(RuntimeError, match="MONGODB_URI"):
        await seed_initial_user(settings)
