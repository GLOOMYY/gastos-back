"""Domain entities for financial transactions."""

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.modules.transactions.domain.enums import (
    ExchangeRateMode,
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
    transfer_id: str | None
    exchange_rate: Decimal | None
    exchange_rate_mode: ExchangeRateMode | None
    exchange_rate_provider: str | None
    exchange_rate_timestamp: datetime | None
    source_amount: Decimal | None
    target_amount: Decimal | None
    source_currency: Currency | None
    target_currency: Currency | None
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
        transfer_id: str | None = None,
        exchange_rate: Decimal | None = None,
        exchange_rate_mode: ExchangeRateMode | None = None,
        exchange_rate_provider: str | None = None,
        exchange_rate_timestamp: datetime | None = None,
        source_amount: Decimal | None = None,
        target_amount: Decimal | None = None,
        source_currency: str | None = None,
        target_currency: str | None = None,
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
            reversal_of_id: Optional original entry being reversed.
            transfer_id: Optional identifier shared by a transfer pair.
            exchange_rate: Optional target units per source unit.
            exchange_rate_mode: Optional market or custom rate mode.
            exchange_rate_provider: Optional origin of the selected rate.
            exchange_rate_timestamp: Optional effective rate timestamp.
            source_amount: Optional amount removed from the source account.
            target_amount: Optional amount added to the target account.
            source_currency: Optional transfer source currency.
            target_currency: Optional transfer target currency.

        Returns:
            A new confirmed transaction without a persistence identifier.

        Raises:
            InvalidTransactionIdentifierError: If a required ID is blank.
            InvalidTransactionAmountError: If monetary metadata is invalid.
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

        clean_transfer_id = cls._clean_optional_identifier(
            transfer_id,
            "transfer_id",
        )
        source_currency_value = (
            Currency.create(source_currency) if source_currency is not None else None
        )
        target_currency_value = (
            Currency.create(target_currency) if target_currency is not None else None
        )
        if transaction_type in {
            TransactionType.TRANSFER_OUT,
            TransactionType.TRANSFER_IN,
        }:
            if (
                clean_transfer_id is None
                or not isinstance(source_amount, Decimal)
                or source_amount <= 0
                or not isinstance(target_amount, Decimal)
                or target_amount <= 0
                or source_currency_value is None
                or target_currency_value is None
            ):
                raise InvalidTransactionAmountError()
            expected_amount = (
                source_amount
                if transaction_type is TransactionType.TRANSFER_OUT
                else target_amount
            )
            if amount != expected_amount:
                raise InvalidTransactionAmountError()
            is_cross_currency = source_currency_value != target_currency_value
            if is_cross_currency:
                if (
                    not isinstance(exchange_rate, Decimal)
                    or exchange_rate <= 0
                    or target_amount != source_amount * exchange_rate
                    or exchange_rate_mode is None
                    or not exchange_rate_provider
                    or exchange_rate_timestamp is None
                    or exchange_rate_timestamp.tzinfo is None
                    or exchange_rate_timestamp.utcoffset() is None
                ):
                    raise InvalidTransactionAmountError()
            elif any(
                value is not None
                for value in (
                    exchange_rate,
                    exchange_rate_mode,
                    exchange_rate_provider,
                    exchange_rate_timestamp,
                )
            ):
                raise InvalidTransactionAmountError()

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
            transfer_id=clean_transfer_id,
            exchange_rate=exchange_rate,
            exchange_rate_mode=exchange_rate_mode,
            exchange_rate_provider=cls._clean_optional_text(exchange_rate_provider),
            exchange_rate_timestamp=(
                exchange_rate_timestamp.astimezone(UTC)
                if exchange_rate_timestamp is not None
                else None
            ),
            source_amount=source_amount,
            target_amount=target_amount,
            source_currency=source_currency_value,
            target_currency=target_currency_value,
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
