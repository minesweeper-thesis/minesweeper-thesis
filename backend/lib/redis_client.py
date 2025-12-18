from typing import AsyncIterator

import redis.asyncio as redis

from backend.config import REDIS_URL

_test_redis_instance = None


async def get_redis() -> AsyncIterator[redis.Redis]:
    async with redis.from_url(REDIS_URL) as client:
        yield client


def reset_test_redis():
    global _test_redis_instance
    _test_redis_instance = None


def decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
