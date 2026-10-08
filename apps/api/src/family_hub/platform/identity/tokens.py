"""Session tokens and CSRF tokens (AUTH-5, AUTH-7)."""

import base64
import hashlib
import hmac
import secrets


def new_session_token() -> str:
    """256 bits of randomness, URL-safe."""
    return secrets.token_urlsafe(32)


def hash_session_token(token: str) -> bytes:
    """Only this hash is stored, so a database leak does not leak live sessions."""
    return hashlib.sha256(token.encode()).digest()


def csrf_token_for(session_token: str, secret_key: str) -> str:
    """CSRF token bound to a session: HMAC-SHA256(secret, session token)."""
    digest = hmac.new(secret_key.encode(), session_token.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def csrf_token_matches(candidate: str, session_token: str, secret_key: str) -> bool:
    return hmac.compare_digest(candidate, csrf_token_for(session_token, secret_key))


def session_cookie_name(secure: bool) -> str:
    """``__Host-`` makes browsers refuse the cookie unless Secure, Path=/ and no Domain."""
    return "__Host-fh_session" if secure else "fh_session"
