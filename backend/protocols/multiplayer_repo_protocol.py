import uuid
from typing import Protocol

from backend.core.multi.session import MultiplayerSession


class MultiplayerRepository(Protocol):
    async def get_session(self, session_id: uuid.UUID) -> MultiplayerSession: ...

    async def save_session(self, multiplayer_session: MultiplayerSession): ...
