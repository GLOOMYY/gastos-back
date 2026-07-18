"""Mappings between account type entities and MongoDB documents."""

from app.modules.account_types.domain.entities import AccountType
from app.modules.account_types.infrastructure.documents import (
    AccountTypeDocument,
)
from app.shared.infrastructure.mongodb.object_id import to_object_id


def account_type_to_document(value: AccountType) -> AccountTypeDocument:
    """Convert a domain account type to its persistence representation."""
    document = AccountTypeDocument(
        user_id=to_object_id(value.user_id) if value.user_id else None,
        code=value.code,
        name=value.name,
        normalized_name=value.normalized_name,
        description=value.description,
        is_active=value.is_active,
        created_at=value.created_at,
        updated_at=value.updated_at,
        schema_version=1,
    )
    if value.id is not None:
        document["_id"] = to_object_id(value.id)
    return document


def document_to_account_type(document: AccountTypeDocument) -> AccountType:
    """Convert a stored account type to a domain entity."""
    user_id = document["user_id"]
    return AccountType(
        id=str(document["_id"]),
        user_id=str(user_id) if user_id is not None else None,
        code=document.get("code"),
        name=document["name"],
        description=document.get("description"),
        is_active=document["is_active"],
        created_at=document["created_at"],
        updated_at=document["updated_at"],
    )
