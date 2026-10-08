"""Login, sessions, and their protections. Rules: docs/platform/identity.md."""

import hashlib
from datetime import timedelta

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import select, update

from family_hub.platform.identity import service
from family_hub.platform.identity.models import AuthSession, User
from family_hub.platform.identity.service import now

from .conftest import Family, login

COOKIE = "__Host-fh_session"
LOGIN = "/api/v1/auth/login"
SESSION = "/api/v1/auth/session"
LOGOUT = "/api/v1/auth/logout"


async def attempt(client: AsyncClient, email: str, password: str) -> int:
    response = await client.post(
        LOGIN, json={"email": email, "password": password}, headers={"X-CSRF-Token": "login"}
    )
    return response.status_code


class TestLogin:
    async def test_returns_user_memberships_and_csrf_token(
        self, client: AsyncClient, family: Family
    ) -> None:
        body = await login(client, family.owner_email)

        assert body["user"]["email"] == family.owner_email  # type: ignore[index]
        assert body["memberships"][0]["role"] == "owner"  # type: ignore[index]
        assert body["memberships"][0]["household_name"] == "Demo Family"  # type: ignore[index]
        assert body["csrf_token"]

    async def test_sets_hardened_session_cookie(self, client: AsyncClient, family: Family) -> None:
        """AUTH-5"""
        response = await client.post(
            LOGIN,
            json={"email": family.owner_email, "password": family.password},
            headers={"X-CSRF-Token": "login"},
        )

        cookie = response.headers["set-cookie"]
        assert cookie.startswith(f"{COOKIE}=")
        for attribute in ("HttpOnly", "Secure", "SameSite=lax", "Path=/"):
            assert attribute in cookie
        assert "Domain" not in cookie

    async def test_email_is_case_insensitive(self, client: AsyncClient, family: Family) -> None:
        await login(client, "  ALICE@Example.com ")

    async def test_unknown_email_and_wrong_password_look_identical(
        self, client: AsyncClient, family: Family
    ) -> None:
        """AUTH-3"""
        wrong_password = await client.post(
            LOGIN,
            json={"email": family.owner_email, "password": "not the password"},
            headers={"X-CSRF-Token": "login"},
        )
        unknown_email = await client.post(
            LOGIN,
            json={"email": "nobody@example.com", "password": "not the password"},
            headers={"X-CSRF-Token": "login"},
        )

        assert wrong_password.status_code == unknown_email.status_code == 401
        assert wrong_password.json() == unknown_email.json()

    async def test_inactive_user_cannot_log_in(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        async with app.state.sessionmaker() as db, db.begin():
            await db.execute(
                update(User).where(User.email == family.owner_email).values(is_active=False)
            )

        assert await attempt(client, family.owner_email, family.password) == 401


class TestRateLimits:
    """AUTH-4"""

    async def test_account_locks_after_five_failures(
        self, client: AsyncClient, family: Family
    ) -> None:
        for _ in range(5):
            assert await attempt(client, family.owner_email, "wrong password!") == 401

        response = await client.post(
            LOGIN,
            json={"email": family.owner_email, "password": family.password},
            headers={"X-CSRF-Token": "login"},
        )
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0

    async def test_lock_is_per_account(self, client: AsyncClient, family: Family) -> None:
        for _ in range(5):
            await attempt(client, family.owner_email, "wrong password!")

        await login(client, family.adult_email)

    async def test_success_resets_failure_count(self, client: AsyncClient, family: Family) -> None:
        for _ in range(4):
            await attempt(client, family.owner_email, "wrong password!")
        await login(client, family.owner_email)

        for _ in range(4):
            assert await attempt(client, family.owner_email, "wrong password!") == 401

    async def test_ip_limited_to_ten_attempts_per_minute(
        self, client: AsyncClient, family: Family
    ) -> None:
        for i in range(10):
            assert await attempt(client, f"user{i}@example.com", "whatever") == 401

        assert await attempt(client, family.owner_email, family.password) == 429


class TestSession:
    async def test_current_session_requires_login(self, client: AsyncClient) -> None:
        assert (await client.get(SESSION)).status_code == 401

    async def test_current_session_after_login(self, client: AsyncClient, family: Family) -> None:
        login_body = await login(client, family.adult_email)

        response = await client.get(SESSION)

        assert response.status_code == 200
        assert response.json()["user"]["email"] == family.adult_email
        assert response.json()["csrf_token"] == login_body["csrf_token"]

    async def test_only_token_hash_is_stored(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        """AUTH-5"""
        await login(client, family.owner_email)
        token = client.cookies[COOKIE]

        async with app.state.sessionmaker() as db:
            stored = await db.scalar(select(AuthSession.token_hash))

        assert stored == hashlib.sha256(token.encode()).digest()

    async def test_idle_session_expires(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        """AUTH-6"""
        await login(client, family.owner_email)
        async with app.state.sessionmaker() as db, db.begin():
            await db.execute(update(AuthSession).values(last_seen_at=now() - timedelta(days=15)))

        assert (await client.get(SESSION)).status_code == 401

    async def test_session_expires_at_absolute_limit(
        self, app: FastAPI, client: AsyncClient, family: Family
    ) -> None:
        """AUTH-6"""
        await login(client, family.owner_email)
        async with app.state.sessionmaker() as db, db.begin():
            await db.execute(update(AuthSession).values(expires_at=now() - timedelta(seconds=1)))

        assert (await client.get(SESSION)).status_code == 401

    async def test_logging_in_again_revokes_previous_session(
        self, client: AsyncClient, family: Family
    ) -> None:
        """AUTH-6"""
        await login(client, family.owner_email)
        first_token = client.cookies[COOKIE]
        await login(client, family.owner_email)

        client.cookies.set(COOKIE, first_token)
        assert (await client.get(SESSION)).status_code == 401


class TestLogout:
    async def test_revokes_session_on_server(self, client: AsyncClient, family: Family) -> None:
        """AUTH-6: a copied token is useless after logout."""
        body = await login(client, family.owner_email)
        token = client.cookies[COOKIE]

        response = await client.post(LOGOUT, headers={"X-CSRF-Token": str(body["csrf_token"])})
        assert response.status_code == 204

        client.cookies.set(COOKIE, token)
        assert (await client.get(SESSION)).status_code == 401

    async def test_requires_matching_csrf_token(self, client: AsyncClient, family: Family) -> None:
        """AUTH-7"""
        await login(client, family.owner_email)

        response = await client.post(LOGOUT, headers={"X-CSRF-Token": "forged"})

        assert response.status_code == 403
        assert (await client.get(SESSION)).status_code == 200

    async def test_succeeds_without_session(self, client: AsyncClient) -> None:
        response = await client.post(LOGOUT, headers={"X-CSRF-Token": "any"})
        assert response.status_code == 204


class TestAccounts:
    async def test_duplicate_email_rejected(self, app: FastAPI, family: Family) -> None:
        async with app.state.sessionmaker() as db, db.begin():
            with pytest.raises(service.EmailAlreadyRegisteredError):
                await service.create_user(
                    db, email="Alice@example.com", display_name="X", password=family.password
                )
