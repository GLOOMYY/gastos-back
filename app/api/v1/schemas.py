"""Shared HTTP schemas for API version 1."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned when the HTTP application is available."""

    status: Literal["ok"]


class ErrorResponse(BaseModel):
    """Standard machine-readable API error response."""

    code: str
    message: str
    details: object | None
    request_id: str
