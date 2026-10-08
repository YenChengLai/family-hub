"""FastAPI dependencies shared by the platform and modules."""

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from family_hub.config import Settings
from family_hub.platform.identity.models import AuthSession, User
from family_hub.platform.identity.service import SessionTimeouts, resolve_session
from family_hub.platform.identity.tokens import session_cookie_name
from family_hub.platform.security.ratelimit import RateLimiter


def get_settings_dep(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


async def get_db(request: Request) -> AsyncIterator[AsyncSession]:
    """One transaction per request: committed on success, rolled back on error."""
    async with request.app.state.sessionmaker() as session, session.begin():
        yield session


def get_rate_limiter(request: Request) -> RateLimiter:
    redis: Redis = request.app.state.redis
    return RateLimiter(redis)


SettingsDep = Annotated[Settings, Depends(get_settings_dep)]
DbDep = Annotated[AsyncSession, Depends(get_db)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]


def timeouts(settings: Settings) -> SessionTimeouts:
    return SessionTimeouts(
        idle=settings.session_idle_timeout, absolute=settings.session_absolute_timeout
    )


@dataclass(frozen=True)
class Principal:
    """The authenticated caller."""

    user: User
    session: AuthSession
    session_token: str


async def get_principal(request: Request, db: DbDep, settings: SettingsDep) -> Principal:
    token = request.cookies.get(session_cookie_name(settings.cookie_secure))
    resolved = (
        await resolve_session(db, token=token, timeouts=timeouts(settings)) if token else None
    )
    if resolved is None or token is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated")
    session, user = resolved
    return Principal(user=user, session=session, session_token=token)


PrincipalDep = Annotated[Principal, Depends(get_principal)]
