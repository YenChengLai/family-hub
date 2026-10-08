from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from family_hub.config import Settings
from family_hub.main import create_app

INTEGRATION_DIR = Path(__file__).parent / "integration"


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Everything under tests/integration needs PostgreSQL and Redis."""
    for item in items:
        if INTEGRATION_DIR in Path(item.path).parents:
            item.add_marker(pytest.mark.integration)


@pytest.fixture
def settings() -> Settings:
    return Settings(environment="test")


@pytest.fixture
async def app(settings: Settings) -> AsyncIterator[FastAPI]:
    app = create_app(settings)
    async with app.router.lifespan_context(app):
        yield app


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    # HTTPS so the client returns Secure cookies, as browsers do.
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://test") as client:
        yield client
