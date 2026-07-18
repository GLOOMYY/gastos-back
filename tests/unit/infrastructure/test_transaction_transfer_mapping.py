"""Persistence mapping tests for transfer metadata."""

from datetime import UTC, datetime
from decimal import Decimal

from bson import Decimal128, ObjectId

from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import ExchangeRateMode, TransactionType
from app.modules.transactions.infrastructure.mappers import (
    document_to_transaction,
    transaction_to_document,
)

USER_ID = "507f1f77bcf86cd799439011"
ACCOUNT_ID = "507f1f77bcf86cd799439014"


def test_transfer_metadata_round_trips_through_decimal128_document() -> None:
    """MongoDB stores exact transfer amounts and rates as Decimal128."""
    transaction = Transaction.create(
        user_id=USER_ID,
        account_id=ACCOUNT_ID,
        transaction_type=TransactionType.TRANSFER_OUT,
        amount=Decimal("400000"),
        currency="COP",
        occurred_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
        transfer_id="transfer-test-id",
        exchange_rate=Decimal("0.00030"),
        exchange_rate_mode=ExchangeRateMode.CUSTOM,
        exchange_rate_provider="custom",
        exchange_rate_timestamp=datetime(2026, 7, 18, 12, tzinfo=UTC),
        source_amount=Decimal("400000"),
        target_amount=Decimal("120.00000"),
        source_currency="COP",
        target_currency="USD",
    )

    document = transaction_to_document(transaction)

    assert document["exchange_rate"] == Decimal128("0.00030")
    assert document["target_amount"] == Decimal128("120.00000")
    assert document["schema_version"] == 2
    document["_id"] = ObjectId("507f1f77bcf86cd799439021")
    restored = document_to_transaction(document)
    assert restored.exchange_rate == Decimal("0.00030")
    assert restored.target_amount == Decimal("120.00000")
    assert restored.exchange_rate_mode is ExchangeRateMode.CUSTOM


def test_non_transfer_document_omits_exchange_metadata() -> None:
    """Regular ledger entries avoid unnecessary null persistence fields."""
    transaction = Transaction.create(
        user_id=USER_ID,
        account_id=ACCOUNT_ID,
        transaction_type=TransactionType.INCOME,
        amount=Decimal("50"),
        currency="COP",
        occurred_at=datetime(2026, 7, 18, 12, tzinfo=UTC),
    )

    document = transaction_to_document(transaction)

    assert "transfer_id" not in document
    assert "exchange_rate" not in document
    assert "source_amount" not in document
