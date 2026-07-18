"""Domain entities for financial accounts."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.accounts.domain.exceptions import (
    InvalidAccountAmountError,
    InvalidAccountNameError,
    InvalidAccountOwnerError,
    InvalidAccountTypeIdError,
)
from app.shared.domain.value_objects import Currency


@dataclass(slots=True)
class Account:
    """User-owned financial account with a stored current balance."""

    id: str | None
    user_id: str
    account_type_id: str
    name: str
    description: str | None
    initial_balance: Decimal
    balance: Decimal
    currency: Currency
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        account_type_id: str,
        name: str,
        initial_balance: Decimal,
        currency: str,
        description: str | None = None,
    ) -> "Account":
        """Create an active financial account.

        Negative initial balances are valid because some account types may
        represent liabilities.

        Args:
            user_id: Identifier of the account owner.
            account_type_id: Selected global or user-owned account type.
            name: User-visible account name.
            initial_balance: Opening balance represented with Decimal.
            currency: Three-letter account currency.
            description: Optional explanatory text.

        Returns:
            A new account whose current balance equals its initial balance.

        Raises:
            InvalidAccountOwnerError: If the owner identifier is blank.
            InvalidAccountTypeIdError: If the type identifier is blank.
            InvalidAccountNameError: If the account name is blank.
            InvalidAccountAmountError: If the balance does not use Decimal.
            InvalidCurrencyError: If the currency code is invalid.
        """
        clean_user_id = user_id.strip()
        if not clean_user_id:
            raise InvalidAccountOwnerError()

        clean_account_type_id = account_type_id.strip()
        if not clean_account_type_id:
            raise InvalidAccountTypeIdError()

        clean_name = name.strip()
        if not clean_name:
            raise InvalidAccountNameError()

        if not isinstance(initial_balance, Decimal):
            raise InvalidAccountAmountError()

        clean_description = (
            description.strip() if description and description.strip() else None
        )
        now = datetime.now(UTC)

        return cls(
            id=None,
            user_id=clean_user_id,
            account_type_id=clean_account_type_id,
            name=clean_name,
            description=clean_description,
            initial_balance=initial_balance,
            balance=initial_balance,
            currency=Currency.create(currency),
            is_active=True,
            created_at=now,
            updated_at=now,
        )

    @property
    def normalized_name(self) -> str:
        """Return the canonical account name used for comparisons."""
        return self.name.casefold()

    def credit(self, amount: Decimal) -> None:
        """Increase the stored balance by a positive amount."""
        self._validate_positive_amount(amount)
        self.balance += amount
        self.updated_at = datetime.now(UTC)

    def debit(self, amount: Decimal) -> None:
        """Decrease the stored balance while allowing negative balances."""
        self._validate_positive_amount(amount)
        self.balance -= amount
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Prevent new operations on the account."""
        self.is_active = False
        self.updated_at = datetime.now(UTC)

    def activate(self) -> None:
        """Allow new operations on the account."""
        self.is_active = True
        self.updated_at = datetime.now(UTC)

    def update_details(self, name: str, description: str | None) -> None:
        """Update non-financial account metadata."""
        clean_name = name.strip()
        if not clean_name:
            raise InvalidAccountNameError()
        self.name = clean_name
        self.description = (
            description.strip()
            if description is not None and description.strip()
            else None
        )
        self.updated_at = datetime.now(UTC)

    @staticmethod
    def _validate_positive_amount(amount: Decimal) -> None:
        """Validate an amount used to change the balance."""
        if not isinstance(amount, Decimal) or amount <= Decimal("0"):
            raise InvalidAccountAmountError(positive_required=True)
