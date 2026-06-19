"""Server-side refresh-token registry (Redis).

Each issued refresh token has a `jti` stored here with a TTL. A token is only
honored if its jti is still present, which lets us:
  - rotate on every refresh (old jti deleted, new one stored)
  - revoke a single session (logout)
  - revoke every session for a user (logout-all / leaked-credential response)

Keys:
  refresh:{jti}        -> user_id        (TTL = refresh lifetime)
  refresh_user:{uid}   -> set of jti     (for logout-all)
"""

import redis.asyncio as aioredis

from core.config import get_settings
from core.security import REFRESH_TOKEN_EXPIRE_SECONDS

settings = get_settings()
_redis = aioredis.from_url(settings.redis_url, decode_responses=True)


def _jti_key(jti: str) -> str:
    return f"refresh:{jti}"


def _user_key(user_id: str) -> str:
    return f"refresh_user:{user_id}"


async def save(jti: str, user_id: str) -> None:
    await _redis.set(_jti_key(jti), user_id, ex=REFRESH_TOKEN_EXPIRE_SECONDS)
    await _redis.sadd(_user_key(user_id), jti)
    await _redis.expire(_user_key(user_id), REFRESH_TOKEN_EXPIRE_SECONDS)


async def is_valid(jti: str) -> bool:
    return bool(await _redis.exists(_jti_key(jti)))


async def revoke(jti: str, user_id: str | None = None) -> None:
    await _redis.delete(_jti_key(jti))
    if user_id:
        await _redis.srem(_user_key(user_id), jti)


async def revoke_all(user_id: str) -> int:
    jtis = await _redis.smembers(_user_key(user_id))
    if jtis:
        await _redis.delete(*[_jti_key(j) for j in jtis])
    await _redis.delete(_user_key(user_id))
    return len(jtis)
