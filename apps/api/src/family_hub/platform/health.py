"""Health endpoints.

These are intentionally public (no authentication): they reveal only
whether the service and its dependencies are reachable.
"""

from typing import Literal

from fastapi import APIRouter, Request, Response, status
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter(prefix="/health", tags=["health"])

CheckStatus = Literal["ok", "error"]


class Liveness(BaseModel):
    status: Literal["ok"]


class Readiness(BaseModel):
    status: CheckStatus
    database: CheckStatus
    redis: CheckStatus


@router.get("", summary="Liveness")
async def liveness() -> Liveness:
    """The process is up. Does not touch dependencies."""
    return Liveness(status="ok")


@router.get("/ready", summary="Readiness", responses={503: {"model": Readiness}})
async def readiness(request: Request, response: Response) -> Readiness:
    """PostgreSQL and Redis are reachable."""
    state = request.app.state
    database: CheckStatus = "ok"
    redis: CheckStatus = "ok"
    try:
        async with state.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    try:
        await state.redis.ping()
    except Exception:
        redis = "error"

    overall: CheckStatus = "ok" if database == redis == "ok" else "error"
    if overall == "error":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return Readiness(status=overall, database=database, redis=redis)
