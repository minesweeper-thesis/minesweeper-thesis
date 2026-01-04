from typing import Annotated

from fastapi import Depends

from backend.lib.redis_client import get_redis_client
from backend.lib.session_lock import SessionLock


def get_session_lock(redis=Depends(get_redis_client)) -> SessionLock:
    return SessionLock(redis)


SessionLockDep = Annotated[SessionLock, Depends(get_session_lock)]
