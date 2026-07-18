"""MongoDB document typing for ledger entries."""

from datetime import datetime
from typing import NotRequired, TypedDict

from bson import Decimal128, ObjectId


class TransactionDocument(TypedDict):
    """Stored immutable financial transaction."""

    _id: NotRequired[ObjectId]
    user_id: ObjectId
    account_id: ObjectId
    category_id: ObjectId | None
    transaction_type: str
    amount: Decimal128
    currency: str
    occurred_at: datetime
    description: str | None
    note: str | None
    reversal_of_id: ObjectId | None
    status: str
    created_at: datetime
    updated_at: datetime
    schema_version: int
