"""Mappings between financial accounts and MongoDB documents."""

from bson import Decimal128

from app.modules.accounts.domain.entities import Account
from app.modules.accounts.infrastructure.documents import AccountDocument
from app.shared.domain.value_objects import Currency
from app.shared.infrastructure.mongodb.object_id import to_object_id


def account_to_document(value: Account) -> AccountDocument:
    """Convert an account entity to a MongoDB document."""
    document = AccountDocument(
        user_id=to_object_id(value.user_id),
        account_type_id=to_object_id(value.account_type_id),
        name=value.name,
        normalized_name=value.normalized_name,
        description=value.description,
        initial_balance=Decimal128(value.initial_balance),
        balance=Decimal128(value.balance),
        currency=value.currency.code,
        is_active=value.is_active,
        created_at=value.created_at,
        updated_at=value.updated_at,
        schema_version=1,
    )
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_account(document: AccountDocument) -> Account:
    """Convert a MongoDB document to an account entity."""
    return Account(
        id=str(document["_id"]),
        user_id=str(document["user_id"]),
        account_type_id=str(document["account_type_id"]),
        name=document["name"],
        description=document.get("description"),
        initial_balance=document["initial_balance"].to_decimal(),
        balance=document["balance"].to_decimal(),
        currency=Currency.create(document["currency"]),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
