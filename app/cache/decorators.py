from __future__ import annotations

import json
import functools
from typing import Any, Callable

from app.cache.redis_client import get_redis
from app.logging.logger import get_logger

logger = get_logger("cache")


def cache(ttl: int = 60):
    """
    Async cache decorator backed by Redis.

    Usage::

        @cache(ttl=60)
        async def get_user(user_id: int):
            ...
    """
    def decorator(fn: Callable) -> Callable:
        @functools.wraps(fn)
        async def wrapper(*args, **kwargs) -> Any:
            key = f"{fn.__module__}.{fn.__qualname__}:{args}:{kwargs}"
            redis = await get_redis()

            cached = await redis.get(key)
            if cached is not None:
                logger.debug(f"Cache HIT  key={key!r}")
                return json.loads(cached)

            logger.debug(f"Cache MISS key={key!r}")
            result = await fn(*args, **kwargs)
            await redis.setex(key, ttl, json.dumps(result, default=str))
            return result

        return wrapper
    return decorator
