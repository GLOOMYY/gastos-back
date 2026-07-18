"""Value objects shared by multiple domain modules."""

from dataclasses import dataclass

from app.shared.domain.exceptions import InvalidCurrencyError


@dataclass(frozen=True, slots=True)
class Currency:
    """Uppercase fiat or cryptocurrency code."""

    code: str

    @classmethod
    def create(cls, value: str) -> "Currency":
        """Create a validated currency code.

        Args:
            value: Currency code supplied by a caller.

        Returns:
            The normalized currency.

        Raises:
            InvalidCurrencyError: If the code is not 3-10 letters long.
        """
        clean_value = value.strip().upper()
        if not 3 <= len(clean_value) <= 10 or not clean_value.isalpha():
            raise InvalidCurrencyError()

        return cls(code=clean_value)

    def __str__(self) -> str:
        """Return the normalized currency code."""
        return self.code
