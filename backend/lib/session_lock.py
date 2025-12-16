import asyncio
import uuid
from contextlib import asynccontextmanager

from redis.asyncio import Redis


class SessionLock:
    def __init__(self, redis: Redis):
        self.redis = redis
        self.lock_prefix = "lock:session:"
        self._is_fake = "fakeredis" in str(type(redis).__module__)

    @asynccontextmanager
    async def acquire(self, session_id: uuid.UUID, timeout=10.0, blocking_timeout=5.0):
        lock_key = f"{self.lock_prefix}{session_id}"

        if self._is_fake:
            end_time = asyncio.get_event_loop().time() + blocking_timeout

            while asyncio.get_event_loop().time() < end_time:
                if await self.redis.set(lock_key, "1", nx=True, ex=int(timeout)):
                    break
                await asyncio.sleep(0.01)
            else:
                raise RuntimeError(f"Failed to acquire lock for session {session_id}")

            try:
                yield
            finally:
                await self.redis.delete(lock_key)
        else:
            lock = self.redis.lock(
                lock_key,
                timeout=timeout,
                blocking_timeout=blocking_timeout,
                thread_local=False,
            )

            acquired = await lock.acquire()
            if not acquired:
                raise RuntimeError(f"Failed to acquire lock for session {session_id}")

            try:
                yield
            finally:
                await lock.release()
