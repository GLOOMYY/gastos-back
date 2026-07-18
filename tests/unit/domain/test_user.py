"""Unit tests for the user domain entity."""

from datetime import UTC

import pytest

from app.modules.users.domain.entities import User
from app.modules.users.domain.enums import UserRole
from app.modules.users.domain.exceptions import EmptyPasswordHashError


def test_create_user_sets_initial_domain_state() -> None:
    """A new user starts active with the only supported role."""
    user = User.create(
        email="User@Example.com",
        password_hash="$argon2id$test-hash",
    )

    assert user.id is None
    assert user.email.value == "User@Example.com"
    assert user.email.normalized == "user@example.com"
    assert user.password_hash == "$argon2id$test-hash"
    assert user.role is UserRole.USER
    assert user.is_active is True
    assert user.created_at.tzinfo is UTC
    assert user.updated_at == user.created_at


@pytest.mark.parametrize("password_hash", ["", " ", "\t\n"])
def test_create_user_rejects_empty_password_hash(
    password_hash: str,
) -> None:
    """A raw or missing password hash cannot enter the entity."""
    with pytest.raises(EmptyPasswordHashError):
        User.create(
            email="user@example.com",
            password_hash=password_hash,
        )


def test_user_can_be_deactivated_and_reactivated() -> None:
    """Activation behavior changes state through explicit entity methods."""
    user = User.create(
        email="user@example.com",
        password_hash="$argon2id$test-hash",
    )

    user.deactivate()

    assert user.is_active is False
    assert user.updated_at >= user.created_at

    user.activate()

    assert user.is_active is True
    assert user.updated_at >= user.created_at
