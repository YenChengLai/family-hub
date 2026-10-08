"""Fixed-window rate limiting in Redis (AUTH-4).

Redis errors propagate, so limits fail closed: if Redis is down, rate-limited
endpoints return an error instead of allowing unlimited attempts.
"""

from dataclasses import dataclass

from redis.asyncio import Redis


@dataclass(frozen=True)
class Limit:
    max_hits: int
    window_seconds: int


class RateLimiter:
    def __init__(self, redis: "Redis") -> None:
        self._redis = redis

    async def hit(self, key: str, limit: Limit) -> tuple[bool, int]:
        """Count one hit. Return ``(allowed, retry_after_seconds)``."""
        async with self._redis.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.expire(key, limit.window_seconds, nx=True)
            pipe.ttl(key)
            count, _, ttl = await pipe.execute()
        return int(count) <= limit.max_hits, max(int(ttl), 1)

    async def exceeded(self, key: str, limit: Limit) -> tuple[bool, int]:
        """Check without counting. Return ``(exceeded, retry_after_seconds)``."""
        async with self._redis.pipeline(transaction=False) as pipe:
            pipe.get(key)
            pipe.ttl(key)
            raw, ttl = await pipe.execute()
        count = int(raw) if raw is not None else 0
        return count >= limit.max_hits, max(int(ttl), 1)

    async def reset(self, key: str) -> None:
        await self._redis.delete(key)
