import asyncio
import logging
from typing import AsyncIterator

import redis.asyncio as redis

from backend.config import REDIS_URL

logger = logging.getLogger(__name__)

_redis_clients: dict[asyncio.AbstractEventLoop, redis.Redis] = {}


async def initialize_redis() -> None:
    loop = asyncio.get_running_loop()

    if loop in _redis_clients:
        return

    client = redis.from_url(REDIS_URL)
    if "localhost" in REDIS_URL:
        await client.config_set("notify-keyspace-events", "Ex")

    _redis_clients[loop] = client
    logger.info(f"Redis client initialized for loop {id(loop)}")


async def shutdown_redis() -> None:
    for loop, client in _redis_clients.items():
        await client.aclose()
        logger.info(f"Redis client closed for loop {id(loop)}")


def get_redis_client() -> redis.Redis:
    loop = asyncio.get_running_loop()
    if loop not in _redis_clients:
        client = redis.from_url(REDIS_URL)
        _redis_clients[loop] = client
        logger.info(f"Redis client lazily initialized for loop {id(loop)}")

    return _redis_clients[loop]


async def get_redis() -> AsyncIterator[redis.Redis]:
    yield get_redis_client()


def decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
