"""HTTP routes for financial account CRUD operations."""

from fastapi import APIRouter, Response, status

from app.api.v1.dependencies import CreateAccountDep
from app.modules.accounts.application.dto import (
    CreateAccountCommand,
    UpdateAccountCommand,
)
from app.modules.accounts.presentation.dependencies import (
    CloseDep,
    GetDep,
    ListDep,
    UpdateDep,
)
from app.modules.accounts.presentation.schemas import (
    AccountResponse,
    CreateAccountRequest,
    UpdateAccountRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("", response_model=AccountResponse, status_code=201)
async def create_account(
    request: CreateAccountRequest,
    current_user: CurrentUserDep,
    use_case: CreateAccountDep,
) -> AccountResponse:
    """Create an account with an optional opening ledger entry."""
    result = await use_case.execute(
        CreateAccountCommand(
            user_id=current_user.id,
            account_type_id=request.account_type_id,
            name=request.name,
            initial_balance=request.initial_balance,
            currency=request.currency,
            description=request.description,
        )
    )
    return AccountResponse.model_validate(result)


@router.get("", response_model=list[AccountResponse])
async def list_accounts(
    current_user: CurrentUserDep,
    use_case: ListDep,
) -> list[AccountResponse]:
    """List the current user's accounts."""
    return [
        AccountResponse.model_validate(value)
        for value in await use_case.execute(current_user.id)
    ]


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: str,
    current_user: CurrentUserDep,
    use_case: GetDep,
) -> AccountResponse:
    """Retrieve an owned account."""
    return AccountResponse.model_validate(
        await use_case.execute(current_user.id, account_id)
    )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    account_id: str,
    request: UpdateAccountRequest,
    current_user: CurrentUserDep,
    use_case: UpdateDep,
) -> AccountResponse:
    """Update an owned account's metadata."""
    result = await use_case.execute(
        UpdateAccountCommand(
            user_id=current_user.id,
            account_id=account_id,
            name=request.name,
            description=request.description,
        )
    )
    return AccountResponse.model_validate(result)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_account(
    account_id: str,
    current_user: CurrentUserDep,
    use_case: CloseDep,
) -> Response:
    """Soft-delete an owned account."""
    await use_case.execute(current_user.id, account_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
