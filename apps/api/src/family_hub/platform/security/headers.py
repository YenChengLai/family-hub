"""Security headers on every response (AUTH-8)."""

from collections.abc import Awaitable, Callable

from fastapi import Request, Response

API_CSP = "default-src 'none'; frame-ancestors 'none'"


def security_headers_middleware(
    docs_paths: frozenset[str],
) -> Callable[[Request, Callable[[Request], Awaitable[Response]]], Awaitable[Response]]:
    async def middleware(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers["X-Content-Type-Options"] = "nosniff"
        headers["Referrer-Policy"] = "same-origin"
        headers["X-Frame-Options"] = "DENY"
        # API responses hold private data: never cache them anywhere.
        headers["Cache-Control"] = "no-store"
        # Interactive docs (development only) load scripts from a CDN.
        if request.url.path not in docs_paths:
            headers["Content-Security-Policy"] = API_CSP
        return response

    return middleware
