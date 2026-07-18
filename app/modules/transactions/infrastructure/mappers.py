"""Mappings between ledger entities and MongoDB documents."""

from bson import Decimal128

from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import (
    ExchangeRateMode,
    TransactionStatus,
    TransactionType,
)
from app.modules.transactions.infrastructure.documents import (
    TransactionDocument,
)
from app.shared.domain.value_objects import Currency
from app.shared.infrastructure.mongodb.object_id import to_object_id


def transaction_to_document(value: Transaction) -> TransactionDocument:
    """Convert an immutable ledger entry to a MongoDB document."""
    document = TransactionDocument(
        user_id=to_object_id(value.user_id),
        account_id=to_object_id(value.account_id),
        category_id=(to_object_id(value.category_id) if value.category_id else None),
        transaction_type=value.transaction_type.value,
        amount=Decimal128(value.amount),
        currency=value.currency.code,
        occurred_at=value.occurred_at,
        description=value.description,
        note=value.note,
        reversal_of_id=(
            to_object_id(value.reversal_of_id) if value.reversal_of_id else None
        ),
        status=value.status.value,
        created_at=value.created_at,
        updated_at=value.updated_at,
        schema_version=2,
    )
    if value.transfer_id is not None:
        document["transfer_id"] = value.transfer_id
    if value.exchange_rate is not None:
        document["exchange_rate"] = Decimal128(value.exchange_rate)
    if value.exchange_rate_mode is not None:
        document["exchange_rate_mode"] = value.exchange_rate_mode.value
    if value.exchange_rate_provider is not None:
        document["exchange_rate_provider"] = value.exchange_rate_provider
    if value.exchange_rate_timestamp is not None:
        document["exchange_rate_timestamp"] = value.exchange_rate_timestamp
    if value.source_amount is not None:
        document["source_amount"] = Decimal128(value.source_amount)
    if value.target_amount is not None:
        document["target_amount"] = Decimal128(value.target_amount)
    if value.source_currency is not None:
        document["source_currency"] = value.source_currency.code
    if value.target_currency is not None:
        document["target_currency"] = value.target_currency.code
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_transaction(document: TransactionDocument) -> Transaction:
    """Convert a MongoDB document to an immutable ledger entity."""
    category_id = document.get("category_id")
    reversal_id = document.get("reversal_of_id")
    exchange_rate = document.get("exchange_rate")
    source_amount = document.get("source_amount")
    target_amount = document.get("target_amount")
    exchange_rate_mode = document.get("exchange_rate_mode")
    source_currency = document.get("source_currency")
    target_currency = document.get("target_currency")
    return Transaction(
        id=str(document["_id"]),
        user_id=str(document["user_id"]),
        account_id=str(document["account_id"]),
        category_id=str(category_id) if category_id is not None else None,
        transaction_type=TransactionType(document["transaction_type"]),
        amount=document["amount"].to_decimal(),
        currency=Currency.create(document["currency"]),
        occurred_at=document["occurred_at"],
        description=document.get("description"),
        note=document.get("note"),
        reversal_of_id=(str(reversal_id) if reversal_id is not None else None),
        transfer_id=document.get("transfer_id"),
        exchange_rate=(
            exchange_rate.to_decimal() if exchange_rate is not None else None
        ),
        exchange_rate_mode=(
            ExchangeRateMode(exchange_rate_mode)
            if exchange_rate_mode is not None
            else None
        ),
        exchange_rate_provider=document.get("exchange_rate_provider"),
        exchange_rate_timestamp=document.get("exchange_rate_timestamp"),
        source_amount=(
            source_amount.to_decimal() if source_amount is not None else None
        ),
        target_amount=(
            target_amount.to_decimal() if target_amount is not None else None
        ),
        source_currency=(
            Currency.create(source_currency) if source_currency is not None else None
        ),
        target_currency=(
            Currency.create(target_currency) if target_currency is not None else None
        ),
        status=TransactionStatus(document["status"]),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
