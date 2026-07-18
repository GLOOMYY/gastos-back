"""Use case for public user registration."""

from app.modules.users.application.dto import CreateUserCommand, UserResult
from app.modules.users.application.mappers import user_to_result
from app.modules.users.application.ports import PasswordHasher
from app.modules.users.domain.entities import User
from app.modules.users.domain.exceptions import (
    InvalidPasswordError,
    UserAlreadyExistsError,
)
from app.modules.users.domain.repositories import UserRepository
from app.modules.users.domain.value_objects import Email

_MIN_PASSWORD_LENGTH = 8
_MAX_PASSWORD_LENGTH = 128


class CreateUser:
    """Register a user with a unique normalized email."""

    def __init__(
        self,
        user_repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        """Initialize the registration use case."""
        self._user_repository = user_repository
        self._password_hasher = password_hasher

    async def execute(self, command: CreateUserCommand) -> UserResult:
        """Register and return a new user.

        Args:
            command: Registration email and raw password.

        Returns:
            The safely exposed registered user.

        Raises:
            InvalidEmailError: If the email is malformed.
            InvalidPasswordError: If the password length is invalid.
            UserAlreadyExistsError: If the email is already registered.
        """
        if not _MIN_PASSWORD_LENGTH <= len(command.password) <= _MAX_PASSWORD_LENGTH:
            raise InvalidPasswordError()

        email = Email.create(command.email)
        existing_user = await self._user_repository.get_by_normalized_email(
            email.normalized,
        )
        if existing_user is not None:
            raise UserAlreadyExistsError()

        user = User.create(
            email=email.value,
            password_hash=self._password_hasher.hash(command.password),
        )
        created_user = await self._user_repository.add(user)

        return user_to_result(created_user)
