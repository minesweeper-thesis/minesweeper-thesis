import uuid
from contextlib import asynccontextmanager

from redis.asyncio import Redis


class SessionLock:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.lock_prefix = "lock:session:"

    @asynccontextmanager
    async def acquire(self, session_id: uuid.UUID, timeout=5.0, blocking_timeout=5.0):
        lock_key = f"{self.lock_prefix}{session_id}"
        lock = self.redis.lock(
            lock_key, timeout=timeout, blocking_timeout=blocking_timeout
        )

        acquired = await lock.acquire()
        if not acquired:
            raise RuntimeError(f"Failed to acquire lock for session {session_id}")

        try:
            yield
        finally:
            await lock.release()
