"""FastAPI CRUD routes for the authenticated user."""

from fastapi import APIRouter, Response, status

from app.api.v1.schemas import ErrorResponse
from app.modules.users.application.dto import (
    DeactivateUserCommand,
    UpdateUserCommand,
)
from app.modules.users.presentation.dependencies import (
    CurrentUserDep,
    DeactivateUserDep,
    UpdateUserDep,
)
from app.modules.users.presentation.schemas import (
    UpdateUserRequest,
    UserResponse,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)


@router.get("/me", response_model=UserResponse)
async def get_authenticated_user(
    current_user: CurrentUserDep,
) -> UserResponse:
    """Return the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_authenticated_user(
    request: UpdateUserRequest,
    current_user: CurrentUserDep,
    use_case: UpdateUserDep,
) -> UserResponse:
    """Update the current user's email or password."""
    result = await use_case.execute(
        UpdateUserCommand(
            user_id=current_user.id,
            email=request.email,
            password=request.password,
        )
    )
    return UserResponse.model_validate(result)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_authenticated_user(
    current_user: CurrentUserDep,
    use_case: DeactivateUserDep,
) -> Response:
    """Soft-delete the current user and revoke refresh sessions."""
    await use_case.execute(DeactivateUserCommand(user_id=current_user.id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
