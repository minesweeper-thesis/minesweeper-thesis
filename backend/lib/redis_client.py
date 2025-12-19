import asyncio
import logging
from typing import AsyncIterator

import redis.asyncio as redis

from backend.config import REDIS_URL

logger = logging.getLogger(__name__)

_redis_client = None


async def initialize_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        return

    client = redis.from_url(REDIS_URL)
    if "localhost" in REDIS_URL:
        await client.config_set("notify-keyspace-events", "Ex")

    _redis_client = client


async def shutdown_redis() -> None:
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        logger.info("Redis client closed")


def get_redis_client() -> redis.Redis:
    global _redis_client

    if asyncio.get_event_loop().is_closed():
        _redis_client = redis.from_url(REDIS_URL)

    return _redis_client  # type: ignore


async def get_redis() -> AsyncIterator[redis.Redis]:
    yield get_redis_client()


def decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
