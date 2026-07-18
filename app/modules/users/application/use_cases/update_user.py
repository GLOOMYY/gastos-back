"""Use case for updating the authenticated user."""

from app.modules.users.application.dto import UpdateUserCommand, UserResult
from app.modules.users.application.mappers import user_to_result
from app.modules.users.application.ports import (
    Clock,
    PasswordHasher,
    RefreshTokenRepository,
)
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    InvalidPasswordError,
    NoUserChangesError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.modules.users.domain.repositories import UserRepository
from app.modules.users.domain.value_objects import Email

_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128


class UpdateUser:
    """Change the authenticated user's email or password."""

    def __init__(
        self,
        user_repository: UserRepository,
        refresh_token_repository: RefreshTokenRepository,
        password_hasher: PasswordHasher,
        clock: Clock,
    ) -> None:
        """Initialize the user update use case."""
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._clock = clock

    async def execute(self, command: UpdateUserCommand) -> UserResult:
        """Apply validated changes to an active user."""
        if command.email is None and command.password is None:
            raise NoUserChangesError()

        user = await self._user_repository.get_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError()
        if not user.is_active:
            raise InactiveUserError()

        if command.email is not None:
            email = Email.create(command.email)
            if email.normalized != user.email.normalized:
                existing_user = await self._user_repository.get_by_normalized_email(
                    email.normalized
                )
                if existing_user is not None:
                    raise UserAlreadyExistsError()
            user.change_email(email.value)

        password_changed = command.password is not None
        if command.password is not None:
            if not (
                _MIN_PASSWORD_LENGTH <= len(command.password) <= _MAX_PASSWORD_LENGTH
            ):
                raise InvalidPasswordError()
            user.change_password_hash(self._password_hasher.hash(command.password))

        await self._user_repository.update(user)

        if password_changed:
            await self._refresh_token_repository.revoke_by_user(
                command.user_id,
                self._clock.now(),
            )

        return user_to_result(user)
