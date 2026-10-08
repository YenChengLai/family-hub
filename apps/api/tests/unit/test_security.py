"""Security behaviour that needs no database: tokens, passwords, CSRF, headers."""

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from family_hub.config import Settings
from family_hub.platform.identity.passwords import WeakPasswordError, check_policy
from family_hub.platform.identity.tokens import (
    csrf_token_for,
    csrf_token_matches,
    hash_session_token,
    new_session_token,
    session_cookie_name,
)


class TestPasswordPolicy:
    """AUTH-2"""

    def test_rejects_short_password(self) -> None:
        with pytest.raises(WeakPasswordError):
            check_policy("a" * 11)

    def test_rejects_overlong_password(self) -> None:
        with pytest.raises(WeakPasswordError):
            check_policy("a" * 129)

    def test_accepts_long_passphrase(self) -> None:
        check_policy("correct horse battery staple")


class TestTokens:
    """AUTH-5, AUTH-7"""

    def test_session_tokens_are_unique_and_long(self) -> None:
        tokens = {new_session_token() for _ in range(100)}
        assert len(tokens) == 100
        assert all(len(t) >= 43 for t in tokens)

    def test_stored_hash_differs_from_token(self) -> None:
        token = new_session_token()
        assert hash_session_token(token) != token.encode()
        assert len(hash_session_token(token)) == 32

    def test_csrf_token_is_bound_to_session_and_secret(self) -> None:
        token = new_session_token()
        csrf = csrf_token_for(token, "secret-a")
        assert csrf_token_matches(csrf, token, "secret-a")
        assert not csrf_token_matches(csrf, new_session_token(), "secret-a")
        assert not csrf_token_matches(csrf, token, "secret-b")

    def test_secure_cookie_uses_host_prefix(self) -> None:
        assert session_cookie_name(secure=True) == "__Host-fh_session"
        assert session_cookie_name(secure=False) == "fh_session"


class TestProductionSettings:
    def test_rejects_default_secret(self) -> None:
        with pytest.raises(ValidationError, match="FH_SECRET_KEY"):
            Settings(environment="production")

    def test_rejects_insecure_cookies(self) -> None:
        with pytest.raises(ValidationError, match="FH_COOKIE_SECURE"):
            Settings(environment="production", secret_key="x" * 32, cookie_secure=False)

    def test_accepts_strong_secret(self) -> None:
        Settings(environment="production", secret_key="x" * 32)


class TestCsrfMiddleware:
    """AUTH-7. Rejected before any route runs, so no database is needed."""

    async def test_unsafe_request_without_header_is_rejected(self, client: AsyncClient) -> None:
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 403
        assert response.json() == {"detail": "CSRF token missing"}

    async def test_login_without_header_is_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/v1/auth/login", json={"email": "a@example.com", "password": "x"}
        )
        assert response.status_code == 403

    async def test_header_not_matching_session_is_rejected(self, client: AsyncClient) -> None:
        client.cookies.set("__Host-fh_session", new_session_token())
        response = await client.post("/api/v1/auth/logout", headers={"X-CSRF-Token": "forged"})
        assert response.status_code == 403
        assert response.json() == {"detail": "CSRF token invalid"}

    async def test_safe_methods_need_no_header(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200


class TestSecurityHeaders:
    """AUTH-8"""

    async def test_api_responses_carry_security_headers(self, client: AsyncClient) -> None:
        headers = (await client.get("/api/v1/health")).headers
        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["Cache-Control"] == "no-store"
        assert headers["X-Frame-Options"] == "DENY"
        assert "frame-ancestors 'none'" in headers["Content-Security-Policy"]

    async def test_docs_page_is_not_blocked_by_csp(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/docs")
        assert response.status_code == 200
        assert "Content-Security-Policy" not in response.headers
