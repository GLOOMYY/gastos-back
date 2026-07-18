"""Use case for updating the authenticated user."""

from app.modules.users.application.dto import UpdateUserCommand, UserResult
from app.modules.users.application.mappers import user_to_result
from app.modules.users.application.ports import (
    Clock,
    PasswordHasher,
    RefreshTokenRepository,
    UserReferenceData,
)
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    InvalidFavoriteCurrencyError,
    InvalidPasswordError,
    InvalidUserCountryError,
    NoUserChangesError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.modules.users.domain.repositories import UserRepository
from app.modules.users.domain.value_objects import CountryCode, Email
from app.shared.domain.value_objects import Currency

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
        reference_data: UserReferenceData | None = None,
    ) -> None:
        """Initialize the user update use case."""
        self._user_repository = user_repository
        self._refresh_token_repository = refresh_token_repository
        self._password_hasher = password_hasher
        self._clock = clock
        self._reference_data = reference_data

    async def execute(self, command: UpdateUserCommand) -> UserResult:
        """Apply validated changes to an active user."""
        if all(
            value is None
            for value in (
                command.email,
                command.password,
                command.favorite_currency,
                command.country_code,
            )
        ):
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

        if command.favorite_currency is not None:
            favorite_currency = Currency.create(command.favorite_currency).code
            if (
                self._reference_data is None
                or not await self._reference_data.currency_exists(favorite_currency)
            ):
                raise InvalidFavoriteCurrencyError()
        if command.country_code is not None:
            country_code = CountryCode.create(command.country_code).value
            if (
                self._reference_data is None
                or not await self._reference_data.country_exists(country_code)
            ):
                raise InvalidUserCountryError()
        user.update_preferences(
            command.favorite_currency,
            command.country_code,
        )

        await self._user_repository.update(user)

        if password_changed:
            await self._refresh_token_repository.revoke_by_user(
                command.user_id,
                self._clock.now(),
            )

        return user_to_result(user)
