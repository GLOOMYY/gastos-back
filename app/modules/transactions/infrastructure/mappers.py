"""Mappings between ledger entities and MongoDB documents."""

from bson import Decimal128

from app.modules.transactions.domain.entities import Transaction
from app.modules.transactions.domain.enums import (
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
        schema_version=1,
    )
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_transaction(document: TransactionDocument) -> Transaction:
    """Convert a MongoDB document to an immutable ledger entity."""
    category_id = document.get("category_id")
    reversal_id = document.get("reversal_of_id")
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
        status=TransactionStatus(document["status"]),
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
