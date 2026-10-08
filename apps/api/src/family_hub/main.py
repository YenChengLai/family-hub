"""Application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from redis.asyncio import Redis

from family_hub.config import Settings, get_settings
from family_hub.db import create_engine, create_sessionmaker
from family_hub.platform import health
from family_hub.platform.identity import router as identity
from family_hub.platform.security.csrf import csrf_middleware
from family_hub.platform.security.headers import security_headers_middleware

API_PREFIX = "/api/v1"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_engine(str(settings.database_url))
        redis = Redis.from_url(str(settings.redis_url))
        app.state.engine = engine
        app.state.sessionmaker = create_sessionmaker(engine)
        app.state.redis = redis
        try:
            yield
        finally:
            await redis.aclose()
            await engine.dispose()

    # Interactive API docs are disabled in production to reduce exposed surface.
    docs_enabled = not settings.is_production
    openapi_url = f"{API_PREFIX}/openapi.json"
    docs_url = f"{API_PREFIX}/docs"
    app = FastAPI(
        title="Family Hub API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url=openapi_url if docs_enabled else None,
        docs_url=docs_url if docs_enabled else None,
        redoc_url=None,
    )
    app.state.settings = settings

    # Middleware runs in reverse order of registration: headers wrap everything.
    app.middleware("http")(
        csrf_middleware(settings, exempt_from_match=frozenset({API_PREFIX + identity.LOGIN_PATH}))
    )
    app.middleware("http")(security_headers_middleware(frozenset({docs_url})))

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health.router)
    api.include_router(identity.router)
    app.include_router(api)
    return app


app = create_app()
