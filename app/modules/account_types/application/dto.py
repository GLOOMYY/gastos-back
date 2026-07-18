"""Application data transfer objects for account types."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CreateAccountTypeCommand:
    """Input required to create a private account type."""

    user_id: str
    name: str
    description: str | None = None
    code: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateAccountTypeCommand:
    """Editable attributes of a private account type."""

    user_id: str
    account_type_id: str
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class AccountTypeResult:
    """Account type data returned by application use cases."""

    id: str
    user_id: str | None
    code: str | None
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
