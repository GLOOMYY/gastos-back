"""Unit tests for authentication cryptographic adapters."""

from app.modules.users.domain.exceptions import (
    InvalidAuthenticationTokenError,
)
from app.modules.users.infrastructure.password_hasher import (
    PasslibPasswordHasher,
)
from app.modules.users.infrastructure.token_service import JoseTokenService


def _token_service() -> JoseTokenService:
    """Build a deterministic-configuration JWT adapter."""
    return JoseTokenService(
        secret_key="test-secret-key-that-is-long-and-private",
        algorithm="HS256",
        access_expire_minutes=30,
        refresh_expire_days=30,
    )


def test_passlib_hasher_uses_argon2_and_verifies_password() -> None:
    """Passwords are stored with Argon2 and verified without plaintext."""
    hasher = PasslibPasswordHasher()

    password_hash = hasher.hash("strong-password")

    assert password_hash.startswith("$argon2")
    assert "strong-password" not in password_hash
    assert hasher.verify("strong-password", password_hash) is True
    assert hasher.verify("wrong-password", password_hash) is False


def test_token_service_distinguishes_access_and_refresh_tokens() -> None:
    """JWT purpose claims prevent one token type from replacing another."""
    service = _token_service()
    access = service.issue_access_token("user-1")
    refresh = service.issue_refresh_token("user-1", "family-1")

    access_claims = service.decode_access_token(access.value)
    refresh_claims = service.decode_refresh_token(refresh.value)

    assert access_claims.user_id == "user-1"
    assert access_claims.family_id is None
    assert refresh_claims.user_id == "user-1"
    assert refresh_claims.family_id == "family-1"

    try:
        service.decode_access_token(refresh.value)
    except InvalidAuthenticationTokenError:
        pass
    else:
        raise AssertionError("A refresh token was accepted as an access token.")


def test_refresh_token_fingerprint_is_stable_and_not_raw_token() -> None:
    """Only a stable SHA-256 fingerprint needs persistence."""
    service = _token_service()

    fingerprint = service.hash_token("raw-refresh-token")

    assert fingerprint == service.hash_token("raw-refresh-token")
    assert fingerprint != "raw-refresh-token"
    assert len(fingerprint) == 64
