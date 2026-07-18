"""Unit tests for the user email value object."""

import pytest

from app.modules.users.domain.exceptions import InvalidEmailError
from app.modules.users.domain.value_objects import Email


def test_email_trims_and_builds_normalized_representation() -> None:
    """Email lookup is case-insensitive without losing display casing."""
    email = Email.create("  User@Example.COM  ")

    assert email.value == "User@Example.COM"
    assert email.normalized == "user@example.com"
    assert str(email) == "User@Example.COM"


@pytest.mark.parametrize(
    "value",
    [
        "",
        "not-an-email",
        "missing-domain@",
        "@missing-local.example",
        "user @example.com",
        "user@example",
    ],
)
def test_email_rejects_invalid_basic_format(value: str) -> None:
    """Malformed addresses cannot become domain values."""
    with pytest.raises(InvalidEmailError):
        Email.create(value)
