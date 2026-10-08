"""CSRF protection for every state-changing request (AUTH-7).

- Every unsafe request must carry an ``X-CSRF-Token`` header. Browsers cannot
  add custom headers to cross-site requests without a CORS preflight, and we
  never enable CORS, so the header's presence alone defeats login CSRF.
- If the request carries a session cookie, the header must equal the CSRF
  token derived from that session. Login is exempt from this match because it
  replaces whatever session the browser had.
"""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from family_hub.config import Settings
from family_hub.platform.identity.tokens import csrf_token_matches, session_cookie_name

SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
HEADER = "x-csrf-token"


def csrf_middleware(
    settings: Settings, exempt_from_match: frozenset[str]
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    cookie_name = session_cookie_name(settings.cookie_secure)
    secret = settings.secret_key.get_secret_value()

    async def middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method in SAFE_METHODS:
            return await call_next(request)

        candidate = request.headers.get(HEADER)
        if not candidate:
            return _forbidden("CSRF token missing")

        session_token = request.cookies.get(cookie_name)
        if (
            session_token
            and request.url.path not in exempt_from_match
            and not csrf_token_matches(candidate, session_token, secret)
        ):
            return _forbidden("CSRF token invalid")

        return await call_next(request)

    return middleware


def _forbidden(detail: str) -> Response:
    return JSONResponse({"detail": detail}, status_code=status.HTTP_403_FORBIDDEN)
