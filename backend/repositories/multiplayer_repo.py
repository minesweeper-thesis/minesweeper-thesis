import uuid

from backend import protocols
from backend.core.multi.session import MultiplayerSession
from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class MultiplayerSessionNotFoundError(Exception):
    pass


sessions: dict[uuid.UUID, MultiplayerSession] = {}
pending_sessions: dict[uuid.UUID, MultiplayerSession] = {}


class MultiplayerRepository(protocols.MultiplayerRepository):

    def __init__(self, session: DBSession):
        self.session = session

    async def get_session(self, session_id: uuid.UUID) -> MultiplayerSession:
        pending = pending_sessions.get(session_id, None)
        multiplayer_session = sessions.get(session_id, pending)
        if not multiplayer_session:
            raise MultiplayerSessionNotFoundError(
                f"Multiplayer session with id {session_id} not found"
            )
        return multiplayer_session

    async def save_session(self, multiplayer_session: MultiplayerSession):
        sessions[multiplayer_session.id] = multiplayer_session

    async def save_pending(self, multiplayer_session: MultiplayerSession):
        pending_sessions[multiplayer_session.id] = multiplayer_session

    async def is_pending(self, session_id: uuid.UUID) -> bool:
        return session_id in pending_sessions

    async def get_pending_for_lobby(
        self, lobby_id: uuid.UUID
    ) -> MultiplayerSession | None:
        for session in pending_sessions.values():
            if session.lobby_id == lobby_id:
                return session
        return None
