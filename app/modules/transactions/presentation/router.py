"""HTTP routes for immutable financial ledger operations."""

from datetime import date, timedelta
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.v1.dependencies import ExpenseDep, IncomeDep, ReverseDep
from app.modules.transactions.application.dto import (
    CashFlowInterval,
    GetCashFlowQuery,
    RegisterTransactionCommand,
    ReverseTransactionCommand,
)
from app.modules.transactions.presentation.dependencies import (
    CashFlowDep,
    GetDep,
    ListDep,
)
from app.modules.transactions.presentation.schemas import (
    CashFlowResponse,
    RegisterTransactionRequest,
    ReverseTransactionRequest,
    TransactionPageResponse,
    TransactionResponse,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def build_command(
    user_id: str,
    request: RegisterTransactionRequest,
) -> RegisterTransactionCommand:
    """Map an HTTP movement request to an application command."""
    return RegisterTransactionCommand(
        user_id=user_id,
        account_id=request.account_id,
        category_id=request.category_id,
        amount=request.amount,
        occurred_at=request.occurred_at,
        description=request.description,
        note=request.note,
    )


@router.post("/income", response_model=TransactionResponse, status_code=201)
async def register_income(
    request: RegisterTransactionRequest,
    current_user: CurrentUserDep,
    use_case: IncomeDep,
) -> TransactionResponse:
    """Atomically register an income and increase the account balance."""
    return TransactionResponse.model_validate(
        await use_case.execute(build_command(current_user.id, request))
    )


@router.post("/expense", response_model=TransactionResponse, status_code=201)
async def register_expense(
    request: RegisterTransactionRequest,
    current_user: CurrentUserDep,
    use_case: ExpenseDep,
) -> TransactionResponse:
    """Atomically register an expense and decrease the account balance."""
    return TransactionResponse.model_validate(
        await use_case.execute(build_command(current_user.id, request))
    )


@router.get("", response_model=TransactionPageResponse)
async def list_transactions(
    current_user: CurrentUserDep,
    use_case: ListDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> TransactionPageResponse:
    """List immutable transactions belonging to the current user."""
    result = await use_case.execute(current_user.id, limit, cursor)
    return TransactionPageResponse.model_validate(result)


@router.get("/cash-flow", response_model=CashFlowResponse)
async def get_cash_flow(
    current_user: CurrentUserDep,
    use_case: CashFlowDep,
    date_from: date | None = None,
    date_to: date | None = None,
    currency: Annotated[str, Query(min_length=3, max_length=3)] = "COP",
    interval: CashFlowInterval = CashFlowInterval.DAY,
) -> CashFlowResponse:
    """Return income, expense, and net series ready for charting."""
    resolved_to = date_to or date.today()
    resolved_from = date_from or (resolved_to - timedelta(days=89))
    result = await use_case.execute(
        GetCashFlowQuery(
            user_id=current_user.id,
            date_from=resolved_from,
            date_to=resolved_to,
            currency=currency,
            interval=interval,
        )
    )
    return CashFlowResponse.model_validate(result)


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: CurrentUserDep,
    use_case: GetDep,
) -> TransactionResponse:
    """Retrieve an owned ledger entry."""
    return TransactionResponse.model_validate(
        await use_case.execute(current_user.id, transaction_id)
    )


@router.post(
    "/{transaction_id}/reversal",
    response_model=TransactionResponse,
    status_code=201,
)
async def reverse_transaction(
    transaction_id: str,
    request: ReverseTransactionRequest,
    current_user: CurrentUserDep,
    use_case: ReverseDep,
) -> TransactionResponse:
    """Append a compensating entry without mutating financial history."""
    result = await use_case.execute(
        ReverseTransactionCommand(
            user_id=current_user.id,
            transaction_id=transaction_id,
            reason=request.reason,
        )
    )
    return TransactionResponse.model_validate(result)
