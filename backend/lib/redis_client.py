import logging
import pickle

import redis.asyncio as redis

from backend.config import REDIS_URL

logger = logging.getLogger(__name__)


_client: redis.Redis | None = None


async def initialize_redis() -> None:
    global _client
    if _client is None:
        _client = redis.from_url(REDIS_URL)
        if "localhost" in REDIS_URL:
            await _client.config_set("notify-keyspace-events", "Ex")


async def shutdown_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        logger.info(f"Redis client closed")


async def get_redis_client() -> redis.Redis:
    global _client
    if _client is None:
        raise RuntimeError("Redis client is not initialized")
    return _client


def encode(data) -> bytes:
    return pickle.dumps(data)


def decode(data: bytes):
    return pickle.loads(data)
