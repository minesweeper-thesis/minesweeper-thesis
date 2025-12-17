import uuid
from typing import Optional, Protocol

from backend.core.multi.session import MultiplayerSession


class SessionNotFound(Exception):
    pass


class MultiplayerRepository(Protocol):
    async def get_session(self, session_id: uuid.UUID) -> MultiplayerSession: ...

    async def save_session(self, multiplayer_session: MultiplayerSession): ...

    async def save_pending(self, multiplayer_session: MultiplayerSession): ...

    async def get_pending_for_lobby(
        self, lobby_id: uuid.UUID
    ) -> Optional[MultiplayerSession]: ...

    async def delete_pending(self, session_id: uuid.UUID): ...


__all__ = ["MultiplayerRepository", "SessionNotFound"]
