import uuid

from backend.core.multiplayer import MultiplayerSession
from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class MultiplayerSessionNotFoundError(Exception):
    pass


class MultiplayerRepository:
    sessions: dict[uuid.UUID, MultiplayerSession] = {}

    def __init__(self, session: DBSession):
        self.session = session

    async def get_session(self, session_id: uuid.UUID) -> MultiplayerSession:
        multiplayer_session = self.sessions.get(session_id)
        if not multiplayer_session:
            raise MultiplayerSessionNotFoundError(
                f"Multiplayer session with id {session_id} not found"
            )
        return multiplayer_session

    async def save_session(self, multiplayer_session: MultiplayerSession):
        self.sessions[multiplayer_session.id] = multiplayer_session
