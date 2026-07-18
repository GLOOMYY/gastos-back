"""FastAPI routes for registration and authenticated sessions."""

from fastapi import APIRouter, Response, status

from app.api.v1.schemas import ErrorResponse
from app.modules.users.application.dto import (
    AuthenticateUserCommand,
    CreateUserCommand,
    LogoutUserCommand,
    RefreshSessionCommand,
)
from app.modules.users.presentation.dependencies import (
    AuthenticateUserDep,
    CreateUserDep,
    CurrentUserDep,
    LogoutUserDep,
    RefreshSessionDep,
)
from app.modules.users.presentation.schemas import (
    LoginRequest,
    LogoutRequest,
    RefreshSessionRequest,
    RegisterUserRequest,
    TokenPairResponse,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    request: RegisterUserRequest,
    use_case: CreateUserDep,
) -> UserResponse:
    """Register a user with an email address and password."""
    result = await use_case.execute(
        CreateUserCommand(
            email=request.email,
            password=request.password,
        )
    )
    return UserResponse.model_validate(result)


@router.post("/login", response_model=TokenPairResponse)
async def login(
    request: LoginRequest,
    use_case: AuthenticateUserDep,
) -> TokenPairResponse:
    """Authenticate a user and start a token session."""
    result = await use_case.execute(
        AuthenticateUserCommand(
            email=request.email,
            password=request.password,
        )
    )
    return TokenPairResponse.model_validate(result)


@router.post("/refresh", response_model=TokenPairResponse)
async def refresh_session(
    request: RefreshSessionRequest,
    use_case: RefreshSessionDep,
) -> TokenPairResponse:
    """Rotate a refresh token and return a new token pair."""
    result = await use_case.execute(
        RefreshSessionCommand(refresh_token=request.refresh_token)
    )
    return TokenPairResponse.model_validate(result)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: LogoutRequest,
    use_case: LogoutUserDep,
) -> Response:
    """Revoke a refresh token without exposing session state."""
    await use_case.execute(LogoutUserCommand(refresh_token=request.refresh_token))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUserDep) -> UserResponse:
    """Return the user represented by the bearer access token."""
    return UserResponse.model_validate(current_user)
