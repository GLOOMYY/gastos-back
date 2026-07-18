"""Mapping helpers for user application results."""

from app.modules.users.application.dto import UserResult
from app.modules.users.domain.entities import User


def user_to_result(user: User) -> UserResult:
    """Map a domain user to a safe application result.

    Args:
        user: Domain user with a persistence identifier.

    Returns:
        User data that excludes the password hash.

    Raises:
        ValueError: If the user has no persistence identifier.
    """
    if user.id is None:
        raise ValueError("A persisted user must have an identifier.")

    return UserResult(
        id=user.id,
        email=user.email.value,
        role=user.role.value,
        favorite_currency=(
            user.favorite_currency.code if user.favorite_currency is not None else None
        ),
        country_code=(
            user.country_code.value if user.country_code is not None else None
        ),
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )
