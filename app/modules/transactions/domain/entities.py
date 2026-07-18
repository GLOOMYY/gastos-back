"""Domain entities for financial transactions."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.transactions.domain.enums import (
    TransactionStatus,
    TransactionType,
)
from app.modules.transactions.domain.exceptions import (
    InvalidTransactionAmountError,
    InvalidTransactionDateError,
    InvalidTransactionIdentifierError,
)
from app.shared.domain.value_objects import Currency


@dataclass(frozen=True, slots=True)
class Transaction:
    """Immutable confirmed entry in a user's financial ledger."""

    id: str | None
    user_id: str
    account_id: str
    category_id: str | None
    transaction_type: TransactionType
    amount: Decimal
    currency: Currency
    occurred_at: datetime
    description: str | None
    note: str | None
    reversal_of_id: str | None
    status: TransactionStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(
        cls,
        user_id: str,
        account_id: str,
        transaction_type: TransactionType,
        amount: Decimal,
        currency: str,
        occurred_at: datetime,
        category_id: str | None = None,
        description: str | None = None,
        note: str | None = None,
        reversal_of_id: str | None = None,
    ) -> "Transaction":
        """Create an immutable confirmed financial transaction.

        Args:
            user_id: Identifier of the transaction owner.
            account_id: Identifier of the affected account.
            transaction_type: Financial meaning of the transaction.
            amount: Positive amount represented with Decimal.
            currency: Three-letter transaction currency.
            occurred_at: Time at which the movement occurred.
            category_id: Optional selected category identifier.
            description: Optional movement description.
            note: Optional private observation.

        Returns:
            A new confirmed transaction without a persistence identifier.

        Raises:
            InvalidTransactionIdentifierError: If a required ID is blank.
            InvalidTransactionAmountError: If amount is not a positive Decimal.
            InvalidTransactionDateError: If occurred_at has no timezone.
            InvalidCurrencyError: If the currency code is invalid.
        """
        clean_user_id = cls._clean_required_identifier(user_id, "user_id")
        clean_account_id = cls._clean_required_identifier(
            account_id,
            "account_id",
        )
        clean_category_id = cls._clean_optional_identifier(
            category_id,
            "category_id",
        )

        invalid_amount = not isinstance(amount, Decimal) or amount == Decimal("0")
        if transaction_type is not TransactionType.INITIAL_BALANCE:
            invalid_amount = invalid_amount or amount < Decimal("0")
        if invalid_amount:
            raise InvalidTransactionAmountError()

        if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
            raise InvalidTransactionDateError()

        now = datetime.now(UTC)

        return cls(
            id=None,
            user_id=clean_user_id,
            account_id=clean_account_id,
            category_id=clean_category_id,
            transaction_type=transaction_type,
            amount=amount,
            currency=Currency.create(currency),
            occurred_at=occurred_at.astimezone(UTC),
            description=cls._clean_optional_text(description),
            note=cls._clean_optional_text(note),
            reversal_of_id=cls._clean_optional_identifier(
                reversal_of_id,
                "reversal_of_id",
            ),
            status=TransactionStatus.CONFIRMED,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    def _clean_required_identifier(value: str, field_name: str) -> str:
        """Return a non-empty required identifier."""
        clean_value = value.strip()
        if not clean_value:
            raise InvalidTransactionIdentifierError(field_name)
        return clean_value

    @staticmethod
    def _clean_optional_identifier(
        value: str | None,
        field_name: str,
    ) -> str | None:
        """Return a clean optional identifier or reject a blank value."""
        if value is None:
            return None
        return Transaction._clean_required_identifier(value, field_name)

    @staticmethod
    def _clean_optional_text(value: str | None) -> str | None:
        """Normalize optional free text."""
        if value is None:
            return None
        clean_value = value.strip()
        return clean_value or None
