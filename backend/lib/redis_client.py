import asyncio
import logging
from typing import AsyncIterator

import redis.asyncio as redis

from backend.config import REDIS_URL

logger = logging.getLogger(__name__)

_redis_clients: dict[int, redis.Redis] = {}


def _get_loop_id() -> int:
    try:
        loop = asyncio.get_running_loop()
        return id(loop)
    except RuntimeError:
        return 0


async def initialize_redis() -> None:
    loop_id = _get_loop_id()
    if loop_id in _redis_clients:
        return

    client = redis.from_url(REDIS_URL)
    await client.config_set("notify-keyspace-events", "Ex")
    _redis_clients[loop_id] = client
    logger.info("Redis client initialized for loop %s: %s", loop_id, client)


async def shutdown_redis() -> None:
    loop_id = _get_loop_id()
    client = _redis_clients.pop(loop_id, None)
    if client is not None:
        await client.aclose()
        logger.info("Redis client closed for loop %s", loop_id)


def get_redis_client() -> redis.Redis:
    loop_id = _get_loop_id()
    if loop_id not in _redis_clients:
        client = redis.from_url(REDIS_URL)
        _redis_clients[loop_id] = client
        logger.debug("Redis client created lazily for loop %s: %s", loop_id, client)
    return _redis_clients[loop_id]


async def get_redis() -> AsyncIterator[redis.Redis]:
    yield get_redis_client()


def set_redis_client_for_loop(
    client: redis.Redis | None, loop_id: int | None = None
) -> None:
    if loop_id is None:
        loop_id = _get_loop_id()
    if client is None:
        _redis_clients.pop(loop_id, None)
    else:
        _redis_clients[loop_id] = client


def clear_all_redis_clients() -> None:
    _redis_clients.clear()


def decode_redis_value(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
