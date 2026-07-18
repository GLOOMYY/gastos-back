"""HTTP routes for account type CRUD operations."""

from fastapi import APIRouter, Response, status

from app.modules.account_types.application.dto import (
    CreateAccountTypeCommand,
    UpdateAccountTypeCommand,
)
from app.modules.account_types.presentation.dependencies import (
    CreateDep,
    DeactivateDep,
    GetDep,
    ListDep,
    UpdateDep,
)
from app.modules.account_types.presentation.schemas import (
    AccountTypeResponse,
    CreateAccountTypeRequest,
    UpdateAccountTypeRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/account-types", tags=["Account types"])


@router.post("", response_model=AccountTypeResponse, status_code=201)
async def create_account_type(
    request: CreateAccountTypeRequest,
    current_user: CurrentUserDep,
    use_case: CreateDep,
) -> AccountTypeResponse:
    """Create an account type private to the current user."""
    result = await use_case.execute(
        CreateAccountTypeCommand(
            user_id=current_user.id,
            name=request.name,
            description=request.description,
            code=request.code,
        )
    )
    return AccountTypeResponse.model_validate(result)


@router.get("", response_model=list[AccountTypeResponse])
async def list_account_types(
    current_user: CurrentUserDep,
    use_case: ListDep,
) -> list[AccountTypeResponse]:
    """List global and private active account types."""
    return [
        AccountTypeResponse.model_validate(item)
        for item in await use_case.execute(current_user.id)
    ]


@router.get("/{account_type_id}", response_model=AccountTypeResponse)
async def get_account_type(
    account_type_id: str,
    current_user: CurrentUserDep,
    use_case: GetDep,
) -> AccountTypeResponse:
    """Retrieve an available account type."""
    return AccountTypeResponse.model_validate(
        await use_case.execute(current_user.id, account_type_id)
    )


@router.put("/{account_type_id}", response_model=AccountTypeResponse)
async def update_account_type(
    account_type_id: str,
    request: UpdateAccountTypeRequest,
    current_user: CurrentUserDep,
    use_case: UpdateDep,
) -> AccountTypeResponse:
    """Update an owned account type."""
    result = await use_case.execute(
        UpdateAccountTypeCommand(
            user_id=current_user.id,
            account_type_id=account_type_id,
            name=request.name,
            description=request.description,
        )
    )
    return AccountTypeResponse.model_validate(result)


@router.delete("/{account_type_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_account_type(
    account_type_id: str,
    current_user: CurrentUserDep,
    use_case: DeactivateDep,
) -> Response:
    """Soft-delete an owned account type."""
    await use_case.execute(current_user.id, account_type_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
