"""Application DTOs for financial accounts."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CreateAccountCommand:
    """Input for account creation."""

    user_id: str
    account_type_id: str
    name: str
    initial_balance: Decimal
    currency: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateAccountCommand:
    """Editable account metadata."""

    user_id: str
    account_id: str
    name: str
    description: str | None = None


@dataclass(frozen=True, slots=True)
class SetFavoriteAccountCommand:
    """Select or clear an owned favorite account."""

    user_id: str
    account_id: str
    is_favorite: bool


@dataclass(frozen=True, slots=True)
class AccountResult:
    """Account information returned to presentation."""

    id: str
    user_id: str
    account_type_id: str
    name: str
    description: str | None
    initial_balance: Decimal
    balance: Decimal
    currency: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    is_favorite: bool = False
