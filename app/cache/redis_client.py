from __future__ import annotations

import redis.asyncio as aioredis
from app.core.config import get_settings
from app.logging.logger import get_logger

settings = get_settings()
logger = get_logger("redis-client")

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        logger.info(f"Redis connected to {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis:
        await _redis.aclose()
        _redis = None
