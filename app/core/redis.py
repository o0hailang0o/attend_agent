from redis.asyncio import Redis
from app.core.settings import settings

redis: Redis | None = None


async def init_redis():
    global redis
    redis = Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        password=settings.redis_password or None,
        decode_responses=True,
    )


async def close_redis():
    if redis:
        await redis.aclose()
