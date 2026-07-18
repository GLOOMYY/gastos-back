"""FastAPI dependency composition for user authentication."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo.asynchronous.database import AsyncDatabase

from app.core.config import Settings
from app.core.exceptions import (
    AuthenticationRequiredError,
    ServiceUnavailableError,
)
from app.modules.users.application.dto import UserResult
from app.modules.users.application.use_cases.authenticate_user import (
    AuthenticateUser,
)
from app.modules.users.application.use_cases.create_user import CreateUser
from app.modules.users.application.use_cases.get_user import GetUser
from app.modules.users.application.use_cases.logout_user import LogoutUser
from app.modules.users.application.use_cases.refresh_session import (
    RefreshSession,
)
from app.modules.users.domain.exceptions import (
    InvalidAuthenticationTokenError,
    UserNotFoundError,
)
from app.modules.users.infrastructure.password_hasher import (
    PasslibPasswordHasher,
)
from app.modules.users.infrastructure.repositories import (
    MongoRefreshTokenRepository,
    MongoUserRepository,
)
from app.modules.users.infrastructure.services import (
    SystemClock,
    UuidGenerator,
)
from app.modules.users.infrastructure.token_service import JoseTokenService
from app.shared.infrastructure.mongodb.client import (
    MongoDatabase,
    MongoDocument,
)

_bearer_scheme = HTTPBearer(auto_error=False)


def get_settings_from_app(request: Request) -> Settings:
    """Return settings used to construct the current application."""
    settings = getattr(request.app.state, "settings", None)
    if not isinstance(settings, Settings):
        raise ServiceUnavailableError("Application settings are unavailable.")
    return settings


def get_database(
    request: Request,
) -> AsyncDatabase[MongoDocument]:
    """Return the connected MongoDB database for this application."""
    mongo_database = getattr(request.app.state, "mongo_database", None)
    if not isinstance(mongo_database, MongoDatabase):
        raise ServiceUnavailableError("MongoDB is unavailable.")
    try:
        return mongo_database.get_database()
    except RuntimeError as error:
        raise ServiceUnavailableError("MongoDB is unavailable.") from error


SettingsDep = Annotated[Settings, Depends(get_settings_from_app)]
DatabaseDep = Annotated[
    AsyncDatabase[MongoDocument],
    Depends(get_database),
]


def get_user_repository(database: DatabaseDep) -> MongoUserRepository:
    """Build the MongoDB user repository."""
    return MongoUserRepository(database)


def get_refresh_token_repository(
    database: DatabaseDep,
) -> MongoRefreshTokenRepository:
    """Build the MongoDB refresh-token repository."""
    return MongoRefreshTokenRepository(database)


@lru_cache
def get_password_hasher() -> PasslibPasswordHasher:
    """Return the shared Argon2 password hasher."""
    return PasslibPasswordHasher()


@lru_cache
def get_clock() -> SystemClock:
    """Return the shared system clock."""
    return SystemClock()


@lru_cache
def get_id_generator() -> UuidGenerator:
    """Return the shared UUID generator."""
    return UuidGenerator()


def get_token_service(settings: SettingsDep) -> JoseTokenService:
    """Build a JWT service from secret application settings."""
    if settings.jwt_secret_key is None:
        raise ServiceUnavailableError("JWT configuration is unavailable.")
    secret_key = settings.jwt_secret_key.get_secret_value()
    if len(secret_key) < 32:
        raise ServiceUnavailableError("JWT configuration is unavailable.")
    return JoseTokenService(
        secret_key=secret_key,
        algorithm=settings.jwt_algorithm,
        access_expire_minutes=settings.access_token_expire_minutes,
        refresh_expire_days=settings.refresh_token_expire_days,
    )


UserRepositoryDep = Annotated[
    MongoUserRepository,
    Depends(get_user_repository),
]
RefreshTokenRepositoryDep = Annotated[
    MongoRefreshTokenRepository,
    Depends(get_refresh_token_repository),
]
PasswordHasherDep = Annotated[
    PasslibPasswordHasher,
    Depends(get_password_hasher),
]
TokenServiceDep = Annotated[JoseTokenService, Depends(get_token_service)]
ClockDep = Annotated[SystemClock, Depends(get_clock)]
IdGeneratorDep = Annotated[UuidGenerator, Depends(get_id_generator)]


def get_create_user_use_case(
    user_repository: UserRepositoryDep,
    password_hasher: PasswordHasherDep,
) -> CreateUser:
    """Compose the registration use case."""
    return CreateUser(user_repository, password_hasher)


def get_authenticate_user_use_case(
    user_repository: UserRepositoryDep,
    refresh_token_repository: RefreshTokenRepositoryDep,
    password_hasher: PasswordHasherDep,
    token_service: TokenServiceDep,
    clock: ClockDep,
    id_generator: IdGeneratorDep,
) -> AuthenticateUser:
    """Compose the login use case."""
    return AuthenticateUser(
        user_repository=user_repository,
        refresh_token_repository=refresh_token_repository,
        password_hasher=password_hasher,
        token_service=token_service,
        clock=clock,
        id_generator=id_generator,
    )


def get_refresh_session_use_case(
    user_repository: UserRepositoryDep,
    refresh_token_repository: RefreshTokenRepositoryDep,
    token_service: TokenServiceDep,
    clock: ClockDep,
) -> RefreshSession:
    """Compose the refresh-token rotation use case."""
    return RefreshSession(
        user_repository=user_repository,
        refresh_token_repository=refresh_token_repository,
        token_service=token_service,
        clock=clock,
    )


def get_logout_user_use_case(
    refresh_token_repository: RefreshTokenRepositoryDep,
    token_service: TokenServiceDep,
    clock: ClockDep,
) -> LogoutUser:
    """Compose the logout use case."""
    return LogoutUser(
        refresh_token_repository=refresh_token_repository,
        token_service=token_service,
        clock=clock,
    )


def get_user_use_case(user_repository: UserRepositoryDep) -> GetUser:
    """Compose the active-user query."""
    return GetUser(user_repository)


CreateUserDep = Annotated[CreateUser, Depends(get_create_user_use_case)]
AuthenticateUserDep = Annotated[
    AuthenticateUser,
    Depends(get_authenticate_user_use_case),
]
RefreshSessionDep = Annotated[
    RefreshSession,
    Depends(get_refresh_session_use_case),
]
LogoutUserDep = Annotated[LogoutUser, Depends(get_logout_user_use_case)]
GetUserDep = Annotated[GetUser, Depends(get_user_use_case)]


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer_scheme),
    ],
    token_service: TokenServiceDep,
    get_user: GetUserDep,
) -> UserResult:
    """Authenticate a bearer access token and return its active user."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationRequiredError()

    claims = token_service.decode_access_token(credentials.credentials)
    try:
        return await get_user.execute(claims.user_id)
    except UserNotFoundError as error:
        raise InvalidAuthenticationTokenError() from error


CurrentUserDep = Annotated[UserResult, Depends(get_current_user)]
