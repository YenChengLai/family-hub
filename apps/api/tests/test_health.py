import pytest
from httpx import AsyncClient

from family_hub.config import Settings


async def test_liveness_is_ok(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.integration
async def test_readiness_ok_when_dependencies_reachable(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}


class TestReadinessWithUnreachableDependencies:
    @pytest.fixture
    def settings(self) -> Settings:
        # Port 1 is reserved and closed, so connections fail fast.
        return Settings(
            environment="test",
            database_url="postgresql+asyncpg://nobody:nothing@127.0.0.1:1/none",
            redis_url="redis://127.0.0.1:1/0",
        )

    async def test_readiness_reports_503(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/health/ready")

        assert response.status_code == 503
        assert response.json() == {"status": "error", "database": "error", "redis": "error"}
