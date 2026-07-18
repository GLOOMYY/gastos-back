"""HTTP schemas for account types."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CreateAccountTypeRequest(BaseModel):
    """Request to create a private account type."""

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=300)
    code: str | None = Field(default=None, min_length=1, max_length=40)


class UpdateAccountTypeRequest(BaseModel):
    """Request to replace editable account type metadata."""

    name: str = Field(min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=300)


class AccountTypeResponse(BaseModel):
    """Public account type representation."""

    id: str
    user_id: str | None
    code: str | None
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
