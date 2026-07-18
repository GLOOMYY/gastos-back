"""Shared HTTP schemas for API version 1."""

from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response returned when the HTTP application is available."""

    status: Literal["ok"]
