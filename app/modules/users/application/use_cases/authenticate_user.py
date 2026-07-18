"""Use case for starting an authenticated user session."""

from app.modules.users.application.dto import (
    AuthenticateUserCommand,
    RefreshTokenRecord,
    TokenPairResult,
)
from app.modules.users.application.ports import (
    Clock,
    IdGenerator,
    PasswordHasher,
    RefreshTokenRepository,
    TokenService,
)
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    InvalidEmailError,
)
from app.modules.users.domain.repositories import UserRepository
from app.modules.users.domain.value_objects import Email


class AuthenticateUser:
    """Validate credentials and issue a persisted token pair."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        token_service: TokenService,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        """Initialize the authentication use case."""
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._token_service = token_service
        self._clock = clock
        self._id_generator = id_generator

    async def execute(
        self,
        command: AuthenticateUserCommand,
    ) -> TokenPairResult:
        """Authenticate a user and create a refresh-token session."""
        try:
            normalized_email = Email.create(command.email).normalized
        except InvalidEmailError:
            self._password_hasher.hash(command.password)
            raise InvalidCredentialsError() from None

        user = await self._user_repository.get_by_normalized_email(
            normalized_email,
        )
        if user is None:
            self._password_hasher.hash(command.password)
            raise InvalidCredentialsError()

        if not self._password_hasher.verify(
            command.password,
            user.password_hash,
        ):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        if user.id is None:
            raise RuntimeError("A persisted user must have an identifier.")

        family_id = self._id_generator.generate()
        access_token = self._token_service.issue_access_token(user.id)
        refresh_token = self._token_service.issue_refresh_token(
            user.id,
            family_id,
        )
        now = self._clock.now()

        await self._refresh_token_repository.add(
            RefreshTokenRecord(
                id=refresh_token.token_id,
                user_id=user.id,
                token_hash=self._token_service.hash_token(
                    refresh_token.value,
                ),
                family_id=family_id,
                expires_at=refresh_token.expires_at,
                revoked_at=None,
                replaced_by_id=None,
                created_at=now,
            )
        )

        return TokenPairResult(
            access_token=access_token.value,
            refresh_token=refresh_token.value,
            access_token_expires_at=access_token.expires_at,
            refresh_token_expires_at=refresh_token.expires_at,
        )
