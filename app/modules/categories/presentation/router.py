"""HTTP routes for category CRUD operations."""

from fastapi import APIRouter, Response, status

from app.modules.categories.application.dto import (
    CreateCategoryCommand,
    UpdateCategoryCommand,
)
from app.modules.categories.domain.enums import CategoryTransactionType
from app.modules.categories.presentation.dependencies import (
    CreateDep,
    DeactivateDep,
    GetDep,
    ListDep,
    UpdateDep,
)
from app.modules.categories.presentation.schemas import (
    CategoryResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
)
from app.modules.users.presentation.dependencies import CurrentUserDep

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(
    request: CreateCategoryRequest,
    current_user: CurrentUserDep,
    use_case: CreateDep,
) -> CategoryResponse:
    """Create a category private to the current user."""
    result = await use_case.execute(
        CreateCategoryCommand(
            user_id=current_user.id,
            name=request.name,
            transaction_type=request.transaction_type,
            description=request.description,
        )
    )
    return CategoryResponse.model_validate(result)


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    current_user: CurrentUserDep,
    use_case: ListDep,
    transaction_type: CategoryTransactionType | None = None,
) -> list[CategoryResponse]:
    """List active global and private categories."""
    values = await use_case.execute(current_user.id, transaction_type)
    return [CategoryResponse.model_validate(value) for value in values]


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: str,
    current_user: CurrentUserDep,
    use_case: GetDep,
) -> CategoryResponse:
    """Retrieve an available category."""
    return CategoryResponse.model_validate(
        await use_case.execute(current_user.id, category_id)
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: str,
    request: UpdateCategoryRequest,
    current_user: CurrentUserDep,
    use_case: UpdateDep,
) -> CategoryResponse:
    """Update an owned category."""
    result = await use_case.execute(
        UpdateCategoryCommand(
            user_id=current_user.id,
            category_id=category_id,
            name=request.name,
            transaction_type=request.transaction_type,
            description=request.description,
        )
    )
    return CategoryResponse.model_validate(result)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_category(
    category_id: str,
    current_user: CurrentUserDep,
    use_case: DeactivateDep,
) -> Response:
    """Soft-delete an owned category."""
    await use_case.execute(current_user.id, category_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
