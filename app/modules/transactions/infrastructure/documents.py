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
    transfer_id: NotRequired[str]
    exchange_rate: NotRequired[Decimal128]
    exchange_rate_mode: NotRequired[str]
    exchange_rate_provider: NotRequired[str]
    exchange_rate_timestamp: NotRequired[datetime]
    source_amount: NotRequired[Decimal128]
    target_amount: NotRequired[Decimal128]
    source_currency: NotRequired[str]
    target_currency: NotRequired[str]
    status: str
    created_at: datetime
    updated_at: datetime
    schema_version: int
