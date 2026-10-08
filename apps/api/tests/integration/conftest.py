"""Integration fixtures: a dedicated ``<db>_test`` database and Redis DB 15.

The database is created if missing and migrated with Alembic once per run;
tables are truncated and Redis flushed after every test.
"""

import asyncio
import os
import sys
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import asyncpg
import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url

from family_hub.config import Settings
from family_hub.platform.households import service as households
from family_hub.platform.households.models import Role
from family_hub.platform.identity import service as identity

API_DIR = Path(__file__).resolve().parents[2]
PASSWORD = "correct horse battery staple"  # noqa: S105 - fictional test credential
TABLES = "platform.sessions, platform.memberships, platform.households, platform.users"


def _test_database_url() -> str:
    url = make_url(str(Settings().database_url))
    return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)


def _test_redis_url() -> str:
    base = str(Settings().redis_url).rsplit("/", 1)[0]
    return f"{base}/15"


@pytest.fixture(scope="session")
async def test_database_url() -> str:
    url = make_url(_test_database_url())
    admin = await asyncpg.connect(
        host=url.host, port=url.port, user=url.username, password=url.password, database="postgres"
    )
    try:
        exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", url.database)
        if not exists:
            await admin.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await admin.close()

    env = {**os.environ, "FH_DATABASE_URL": str(url.render_as_string(hide_password=False))}
    process = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "alembic", "upgrade", "head", cwd=API_DIR, env=env
    )
    if await process.wait() != 0:
        raise RuntimeError("alembic upgrade failed for the test database")
    return url.render_as_string(hide_password=False)


@pytest.fixture
def settings(test_database_url: str) -> Settings:
    return Settings(
        environment="test",
        database_url=test_database_url,
        redis_url=_test_redis_url(),
    )


@pytest.fixture(autouse=True)
async def clean_state(app: FastAPI) -> AsyncIterator[None]:
    yield
    async with app.state.engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    await app.state.redis.flushdb()


@dataclass(frozen=True)
class Family:
    owner_email: str = "alice@example.com"
    adult_email: str = "bob@example.com"
    password: str = PASSWORD


@pytest.fixture
async def family(app: FastAPI) -> Family:
    """A fictional household: Alice (owner) and Bob (adult)."""
    fam = Family()
    async with app.state.sessionmaker() as db, db.begin():
        alice = await identity.create_user(
            db, email=fam.owner_email, display_name="Alice", password=PASSWORD
        )
        bob = await identity.create_user(
            db, email=fam.adult_email, display_name="Bob", password=PASSWORD
        )
        household = await households.create_household(db, name="Demo Family", owner=alice)
        await households.add_member(db, household_id=household.id, user=bob, role=Role.ADULT)
    return fam


async def login(client: AsyncClient, email: str, password: str = PASSWORD) -> dict[str, object]:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
        headers={"X-CSRF-Token": "login"},
    )
    assert response.status_code == 200, response.text
    body: dict[str, object] = response.json()
    return body
