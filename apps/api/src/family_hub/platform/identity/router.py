"""Login, logout, and current session. Rules: docs/platform/identity.md."""

import hashlib

from fastapi import APIRouter, HTTPException, Request, Response, status

from family_hub.config import Settings
from family_hub.platform.dependencies import (
    DbDep,
    PrincipalDep,
    RateLimiterDep,
    SettingsDep,
    timeouts,
)
from family_hub.platform.households.service import memberships_of
from family_hub.platform.identity import service
from family_hub.platform.identity.models import User
from family_hub.platform.identity.schemas import LoginRequest, MembershipOut, SessionOut, UserOut
from family_hub.platform.identity.tokens import csrf_token_for, session_cookie_name
from family_hub.platform.security.ratelimit import Limit

router = APIRouter(prefix="/auth", tags=["auth"])

LOGIN_PATH = "/auth/login"

# AUTH-4
LOGIN_PER_IP = Limit(max_hits=10, window_seconds=60)
FAILURES_PER_ACCOUNT = Limit(max_hits=5, window_seconds=15 * 60)

INVALID_CREDENTIALS = "Invalid email or password"


def _too_many(retry_after: int) -> HTTPException:
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "Too many login attempts. Try again later.",
        headers={"Retry-After": str(retry_after)},
    )


def _account_key(email: str) -> str:
    # Hash so raw e-mail addresses are not stored in Redis.
    digest = hashlib.sha256(service.normalize_email(email).encode()).hexdigest()
    return f"rl:login:fail:{digest}"


async def _session_out(db: DbDep, user: User, token: str, settings: Settings) -> SessionOut:
    memberships = await memberships_of(db, user.id)
    return SessionOut(
        user=UserOut(id=user.id, email=user.email, display_name=user.display_name),
        memberships=[
            MembershipOut(household_id=m.household_id, household_name=m.household_name, role=m.role)
            for m in memberships
        ],
        csrf_token=csrf_token_for(token, settings.secret_key.get_secret_value()),
    )


@router.post("/login", summary="Log in")
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    limiter: RateLimiterDep,
) -> SessionOut:
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = await limiter.hit(f"rl:login:ip:{client_ip}", LOGIN_PER_IP)
    if not allowed:
        raise _too_many(retry_after)

    account_key = _account_key(body.email)
    locked, retry_after = await limiter.exceeded(account_key, FAILURES_PER_ACCOUNT)
    if locked:
        raise _too_many(retry_after)

    user = await service.authenticate(db, email=body.email, password=body.password)
    if user is None:
        await limiter.hit(account_key, FAILURES_PER_ACCOUNT)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS)

    await limiter.reset(account_key)
    cookie_name = session_cookie_name(settings.cookie_secure)
    previous = request.cookies.get(cookie_name)
    if previous:
        # Logging in again replaces any session this browser already had.
        await service.revoke_session(db, token=previous)
    token = await service.start_session(
        db,
        user=user,
        timeouts=timeouts(settings),
        user_agent=request.headers.get("user-agent"),
    )
    response.set_cookie(
        cookie_name,
        token,
        max_age=int(settings.session_absolute_timeout.total_seconds()),
        path="/",
        secure=settings.cookie_secure,
        httponly=True,
        samesite="lax",
    )
    return await _session_out(db, user, token, settings)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Log out")
async def logout(request: Request, response: Response, db: DbDep, settings: SettingsDep) -> None:
    """Revoke the current session, if any, and clear the cookie. Always succeeds."""
    cookie_name = session_cookie_name(settings.cookie_secure)
    token = request.cookies.get(cookie_name)
    if token:
        await service.revoke_session(db, token=token)
    response.delete_cookie(
        cookie_name, path="/", secure=settings.cookie_secure, httponly=True, samesite="lax"
    )


@router.get("/session", summary="Current session")
async def current_session(principal: PrincipalDep, db: DbDep, settings: SettingsDep) -> SessionOut:
    return await _session_out(db, principal.user, principal.session_token, settings)
