"""Lightweight fixed-window rate limiting backed by Redis.

Exposed as a dependency factory so sensitive endpoints can opt in:

    _: Annotated[None, Depends(rate_limit("login", 10, 60))]

Keyed by client IP. Fails open (allows the request) if Redis is unreachable, so
a Redis blip never locks everyone out.
"""

from typing import Annotated

import redis.asyncio as aioredis
import structlog
from fastapi import Depends, HTTPException, Request, status

from core.config import get_settings
from core.dependencies import get_client_ip

settings = get_settings()
log = structlog.get_logger()

_redis = aioredis.from_url(settings.redis_url, decode_responses=True)


def rate_limit(name: str, limit: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        if not settings.rate_limit_enabled:
            return
        ip = get_client_ip(request)
        key = f"rl:{name}:{ip}"
        try:
            count = await _redis.incr(key)
            if count == 1:
                await _redis.expire(key, window_seconds)
            if count > limit:
                ttl = await _redis.ttl(key)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many requests. Try again in {max(ttl, 1)}s.",
                    headers={"Retry-After": str(max(ttl, 1))},
                )
        except HTTPException:
            raise
        except Exception as e:  # noqa: BLE001 — never let a Redis hiccup block traffic
            log.warning("ratelimit.unavailable", error=str(e))

    return dependency


# Convenience aliases for common buckets.
LoginRate = Annotated[None, Depends(rate_limit("login", 10, 60))]
RefreshRate = Annotated[None, Depends(rate_limit("refresh", 30, 60))]
SignupRate = Annotated[None, Depends(rate_limit("signup", 25, 3600))]
