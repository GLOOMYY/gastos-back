"""Value objects for the users domain."""

import re
from dataclasses import dataclass

from app.modules.users.domain.exceptions import InvalidEmailError

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_MAX_EMAIL_LENGTH = 254


@dataclass(frozen=True, slots=True)
class Email:
    """Validated email address with a canonical lookup representation."""

    value: str
    normalized: str

    @classmethod
    def create(cls, value: str) -> "Email":
        """Create an email value object from untrusted text.

        Args:
            value: Email address supplied by a caller.

        Returns:
            A validated email preserving display text and normalized for
            case-insensitive lookup.

        Raises:
            InvalidEmailError: If the address has an invalid basic format.
        """
        cleaned_value = value.strip()

        if (
            not cleaned_value
            or len(cleaned_value) > _MAX_EMAIL_LENGTH
            or _EMAIL_PATTERN.fullmatch(cleaned_value) is None
        ):
            raise InvalidEmailError()

        return cls(
            value=cleaned_value,
            normalized=cleaned_value.lower(),
        )

    def __str__(self) -> str:
        """Return the display representation of the email address."""
        return self.value
