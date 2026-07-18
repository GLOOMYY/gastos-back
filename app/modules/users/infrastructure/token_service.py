"""JWT authentication-token adapter."""

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from uuid import uuid4

from jose import JWTError, jwt  # type: ignore[import-untyped]

from app.modules.users.application.dto import (
    IssuedRefreshToken,
    IssuedToken,
    TokenClaims,
)
from app.modules.users.domain.exceptions import (
    InvalidAuthenticationTokenError,
)

_ACCESS_TOKEN_TYPE = "access"
_REFRESH_TOKEN_TYPE = "refresh"


class JoseTokenService:
    """Issue and validate signed JWT access and refresh tokens."""

    def __init__(
        self,
        secret_key: str,
        algorithm: str,
        access_expire_minutes: int,
        refresh_expire_days: int,
    ) -> None:
        """Initialize JWT signing configuration."""
        if not secret_key:
            raise ValueError("JWT secret key cannot be empty.")
        self._secret_key = secret_key
        self._algorithm = algorithm
        self._access_expire_minutes = access_expire_minutes
        self._refresh_expire_days = refresh_expire_days

    def issue_access_token(self, user_id: str) -> IssuedToken:
        """Issue a signed short-lived access token."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self._access_expire_minutes)
        token = self._encode(
            user_id=user_id,
            token_id=str(uuid4()),
            token_type=_ACCESS_TOKEN_TYPE,
            issued_at=now,
            expires_at=expires_at,
        )
        return IssuedToken(value=token, expires_at=expires_at)

    def issue_refresh_token(
        self,
        user_id: str,
        family_id: str,
    ) -> IssuedRefreshToken:
        """Issue a signed refresh token within a rotation family."""
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self._refresh_expire_days)
        token_id = str(uuid4())
        token = self._encode(
            user_id=user_id,
            token_id=token_id,
            token_type=_REFRESH_TOKEN_TYPE,
            issued_at=now,
            expires_at=expires_at,
            family_id=family_id,
        )
        return IssuedRefreshToken(
            value=token,
            token_id=token_id,
            family_id=family_id,
            expires_at=expires_at,
        )

    def decode_access_token(self, token: str) -> TokenClaims:
        """Validate an access token and return trusted claims."""
        return self._decode(token, expected_type=_ACCESS_TOKEN_TYPE)

    def decode_refresh_token(self, token: str) -> TokenClaims:
        """Validate a refresh token and return trusted claims."""
        return self._decode(token, expected_type=_REFRESH_TOKEN_TYPE)

    def hash_token(self, token: str) -> str:
        """Return the SHA-256 fingerprint stored for a refresh token."""
        return sha256(token.encode("utf-8")).hexdigest()

    def _encode(
        self,
        user_id: str,
        token_id: str,
        token_type: str,
        issued_at: datetime,
        expires_at: datetime,
        family_id: str | None = None,
    ) -> str:
        """Encode common trusted claims into a signed JWT."""
        claims: dict[str, object] = {
            "sub": user_id,
            "jti": token_id,
            "type": token_type,
            "iat": issued_at,
            "exp": expires_at,
        }
        if family_id is not None:
            claims["family_id"] = family_id
        return jwt.encode(
            claims,
            self._secret_key,
            algorithm=self._algorithm,
        )

    def _decode(self, token: str, expected_type: str) -> TokenClaims:
        """Decode and validate JWT structure and token purpose."""
        try:
            claims = jwt.decode(
                token,
                self._secret_key,
                algorithms=[self._algorithm],
            )
            user_id = claims.get("sub")
            token_id = claims.get("jti")
            token_type = claims.get("type")
            expires_at = claims.get("exp")
            family_id = claims.get("family_id")

            if (
                not isinstance(user_id, str)
                or not user_id
                or not isinstance(token_id, str)
                or not token_id
                or token_type != expected_type
                or not isinstance(expires_at, (int, float))
                or (family_id is not None and not isinstance(family_id, str))
                or (expected_type == _REFRESH_TOKEN_TYPE and not family_id)
            ):
                raise InvalidAuthenticationTokenError()

            return TokenClaims(
                user_id=user_id,
                token_id=token_id,
                expires_at=datetime.fromtimestamp(expires_at, UTC),
                family_id=family_id,
            )
        except (JWTError, ValueError, TypeError) as error:
            raise InvalidAuthenticationTokenError() from error
