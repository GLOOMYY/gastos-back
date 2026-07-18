"""Translation of application failures to the standard HTTP error format."""

from collections.abc import Mapping
import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.modules.account_types.domain.exceptions import (
    AccountTypeAccessDeniedError,
    AccountTypeNameAlreadyExistsError,
    AccountTypeNotFoundError,
    InvalidAccountTypeNameError,
    InvalidAccountTypeOwnerError,
)
from app.modules.accounts.domain.exceptions import (
    AccountNameAlreadyExistsError,
    AccountNotFoundError,
    InactiveAccountError,
    InvalidAccountAmountError,
    InvalidAccountNameError,
    InvalidAccountOwnerError,
    InvalidAccountTypeIdError,
)
from app.modules.categories.domain.exceptions import (
    CategoryAccessDeniedError,
    CategoryNameAlreadyExistsError,
    CategoryNotFoundError,
    InvalidCategoryNameError,
    InvalidCategoryOwnerError,
)
from app.modules.transactions.domain.exceptions import (
    InvalidTransactionAmountError,
    InvalidTransactionCategoryError,
    InvalidTransactionCursorError,
    InvalidCashFlowRangeError,
    InvalidTransactionDateError,
    InvalidTransactionIdentifierError,
    TransactionAlreadyReversedError,
    TransactionCannotBeReversedError,
    TransactionNotFoundError,
)
from app.modules.users.domain.exceptions import (
    InactiveUserError,
    InvalidAuthenticationTokenError,
    InvalidCredentialsError,
    InvalidEmailError,
    InvalidPasswordError,
    NoUserChangesError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.shared.domain.exceptions import InvalidCurrencyError

logger = logging.getLogger(__name__)


class AuthenticationRequiredError(Exception):
    """Raised when a protected endpoint receives no bearer token."""


class ServiceUnavailableError(Exception):
    """Raised when required runtime configuration is unavailable."""


def register_exception_handlers(app: FastAPI) -> None:
    """Register HTTP translations for known application exceptions."""

    @app.exception_handler(UserAlreadyExistsError)
    async def user_already_exists_handler(
        request: Request,
        exc: UserAlreadyExistsError,
    ) -> JSONResponse:
        """Translate duplicate registration to HTTP conflict."""
        return _error_response(
            request,
            status.HTTP_409_CONFLICT,
            "user_already_exists",
            str(exc),
        )

    @app.exception_handler(InvalidEmailError)
    async def invalid_email_handler(
        request: Request,
        exc: InvalidEmailError,
    ) -> JSONResponse:
        """Translate malformed email to an unprocessable request."""
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_email",
            str(exc),
        )

    @app.exception_handler(InvalidPasswordError)
    async def invalid_password_handler(
        request: Request,
        exc: InvalidPasswordError,
    ) -> JSONResponse:
        """Translate password policy failure to an unprocessable request."""
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "invalid_password",
            str(exc),
        )

    @app.exception_handler(NoUserChangesError)
    async def no_user_changes_handler(
        request: Request,
        exc: NoUserChangesError,
    ) -> JSONResponse:
        """Translate an empty user update to an unprocessable request."""
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "no_user_changes",
            str(exc),
        )

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentialsError,
    ) -> JSONResponse:
        """Translate rejected credentials without revealing which failed."""
        return _error_response(
            request,
            status.HTTP_401_UNAUTHORIZED,
            "invalid_credentials",
            str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InvalidAuthenticationTokenError)
    async def invalid_token_handler(
        request: Request,
        exc: InvalidAuthenticationTokenError,
    ) -> JSONResponse:
        """Translate invalid authentication tokens to unauthorized."""
        return _error_response(
            request,
            status.HTTP_401_UNAUTHORIZED,
            "invalid_authentication_token",
            str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AuthenticationRequiredError)
    async def authentication_required_handler(
        request: Request,
        exc: AuthenticationRequiredError,
    ) -> JSONResponse:
        """Translate missing bearer credentials to unauthorized."""
        return _error_response(
            request,
            status.HTTP_401_UNAUTHORIZED,
            "authentication_required",
            "Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(InactiveUserError)
    async def inactive_user_handler(
        request: Request,
        exc: InactiveUserError,
    ) -> JSONResponse:
        """Translate inactive users to forbidden."""
        return _error_response(
            request,
            status.HTTP_403_FORBIDDEN,
            "inactive_user",
            str(exc),
        )

    @app.exception_handler(UserNotFoundError)
    async def user_not_found_handler(
        request: Request,
        exc: UserNotFoundError,
    ) -> JSONResponse:
        """Translate missing users to not found."""
        return _error_response(
            request,
            status.HTTP_404_NOT_FOUND,
            "user_not_found",
            str(exc),
        )

    async def domain_validation_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Translate domain input validation failures."""
        code = exc.__class__.__name__.removesuffix("Error")
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            _to_snake_case(code),
            str(exc),
        )

    for validation_exception in (
        InvalidAccountTypeNameError,
        InvalidAccountTypeOwnerError,
        InvalidCategoryNameError,
        InvalidCategoryOwnerError,
        InvalidAccountAmountError,
        InvalidAccountNameError,
        InvalidAccountOwnerError,
        InvalidAccountTypeIdError,
        InvalidTransactionAmountError,
        InvalidTransactionCategoryError,
        InvalidTransactionCursorError,
        InvalidCashFlowRangeError,
        InvalidTransactionDateError,
        InvalidTransactionIdentifierError,
        InvalidCurrencyError,
    ):
        app.add_exception_handler(
            validation_exception,
            domain_validation_handler,
        )

    async def resource_not_found_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Translate missing financial resources."""
        resource = exc.__class__.__name__.removesuffix("NotFoundError")
        return _error_response(
            request,
            status.HTTP_404_NOT_FOUND,
            f"{_to_snake_case(resource)}_not_found",
            str(exc),
        )

    for not_found_exception in (
        AccountTypeNotFoundError,
        CategoryNotFoundError,
        AccountNotFoundError,
        TransactionNotFoundError,
    ):
        app.add_exception_handler(
            not_found_exception,
            resource_not_found_handler,
        )

    async def resource_access_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Translate catalog ownership failures."""
        return _error_response(
            request,
            status.HTTP_403_FORBIDDEN,
            "resource_access_denied",
            str(exc),
        )

    for access_exception in (
        AccountTypeAccessDeniedError,
        CategoryAccessDeniedError,
    ):
        app.add_exception_handler(access_exception, resource_access_handler)

    async def resource_conflict_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Translate financial state and uniqueness conflicts."""
        code = exc.__class__.__name__.removesuffix("Error")
        return _error_response(
            request,
            status.HTTP_409_CONFLICT,
            _to_snake_case(code),
            str(exc),
        )

    for conflict_exception in (
        AccountTypeNameAlreadyExistsError,
        CategoryNameAlreadyExistsError,
        AccountNameAlreadyExistsError,
        InactiveAccountError,
        TransactionAlreadyReversedError,
        TransactionCannotBeReversedError,
    ):
        app.add_exception_handler(conflict_exception, resource_conflict_handler)

    @app.exception_handler(ServiceUnavailableError)
    async def service_unavailable_handler(
        request: Request,
        exc: ServiceUnavailableError,
    ) -> JSONResponse:
        """Translate absent runtime integrations to unavailable."""
        return _error_response(
            request,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            "service_unavailable",
            str(exc),
        )

    @app.exception_handler(RequestValidationError)
    async def request_validation_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        """Return Pydantic failures using the standard error envelope."""
        return _error_response(
            request,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "request_validation_error",
            "The request data is invalid.",
            details=jsonable_encoder(exc.errors()),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ) -> JSONResponse:
        """Return framework-generated HTTP failures in the standard format."""
        code = "http_error"
        message = "The request could not be completed."
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "not_found"
            message = "The requested resource was not found."
        elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
            code = "method_not_allowed"
            message = "The HTTP method is not allowed for this resource."
        return _error_response(
            request,
            exc.status_code,
            code,
            message,
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Hide unexpected internal failures and retain correlation context."""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.exception(
            "Unhandled application error.",
            extra={"request_id": request_id},
        )
        return _error_response(
            request,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            "internal_server_error",
            "An unexpected internal error occurred.",
        )


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: object | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    """Build the standard API error envelope."""
    request_id = getattr(request.state, "request_id", "unknown")
    content: dict[str, Any] = {
        "code": code,
        "message": message,
        "details": details,
        "request_id": request_id,
    }
    return JSONResponse(
        status_code=status_code,
        content=content,
        headers=headers,
    )


def _to_snake_case(value: str) -> str:
    """Convert a PascalCase exception fragment to a stable error code."""
    characters: list[str] = []
    for index, character in enumerate(value):
        if character.isupper() and index > 0:
            characters.append("_")
        characters.append(character.lower())
    return "".join(characters)
