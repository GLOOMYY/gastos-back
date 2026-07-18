"""List immutable ledger entries using an opaque cursor."""

import base64
from datetime import datetime
import json
import re

from app.modules.transactions.application.dto import TransactionPageResult
from app.modules.transactions.application.use_cases.get_transaction import (
    to_result,
)
from app.modules.transactions.domain.exceptions import (
    InvalidTransactionCursorError,
)
from app.modules.transactions.domain.repositories import TransactionRepository

_OBJECT_ID_PATTERN = re.compile(r"^[0-9a-fA-F]{24}$")


class ListTransactions:
    """List a user's financial transaction history."""

    def __init__(self, repository: TransactionRepository) -> None:
        """Initialize the use case."""
        self._repository = repository

    async def execute(
        self,
        user_id: str,
        limit: int,
        cursor: str | None = None,
    ) -> TransactionPageResult:
        """Return one deterministic page and an opaque continuation cursor."""
        if limit < 1 or limit > 100:
            raise ValueError("Transaction page size must be between 1 and 100.")
        decoded_cursor = self._decode_cursor(cursor) if cursor else None
        values = await self._repository.list_page(
            user_id,
            limit + 1,
            decoded_cursor,
        )
        has_more = len(values) > limit
        page_values = values[:limit]
        next_cursor = None
        if has_more and page_values:
            last = page_values[-1]
            if last.id is None:
                raise ValueError("A persisted transaction has no identifier.")
            next_cursor = self._encode_cursor(last.occurred_at, last.id)
        return TransactionPageResult(
            items=[to_result(value) for value in page_values],
            next_cursor=next_cursor,
            has_more=has_more,
        )

    @staticmethod
    def _encode_cursor(occurred_at: datetime, transaction_id: str) -> str:
        """Encode deterministic ordering fields without exposing semantics."""
        payload = json.dumps(
            {"occurred_at": occurred_at.isoformat(), "id": transaction_id},
            separators=(",", ":"),
        ).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")

    @staticmethod
    def _decode_cursor(cursor: str) -> tuple[datetime, str]:
        """Validate and decode an opaque continuation cursor."""
        try:
            padded = cursor + "=" * (-len(cursor) % 4)
            payload = json.loads(base64.urlsafe_b64decode(padded).decode())
            occurred_at = datetime.fromisoformat(payload["occurred_at"])
            transaction_id = payload["id"]
            if (
                occurred_at.tzinfo is None
                or not isinstance(transaction_id, str)
                or _OBJECT_ID_PATTERN.fullmatch(transaction_id) is None
            ):
                raise ValueError
        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            raise InvalidTransactionCursorError() from error
        return occurred_at, transaction_id
