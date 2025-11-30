import uuid

from backend.core.multi.session import MultiplayerSession
from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class MultiplayerSessionNotFoundError(Exception):
    pass


sessions: dict[uuid.UUID, MultiplayerSession] = {}


class MultiplayerRepository:

    def __init__(self, session: DBSession):
        self.session = session

    async def get_session(self, session_id: uuid.UUID) -> MultiplayerSession:
        multiplayer_session = sessions.get(session_id)
        if not multiplayer_session:
            raise MultiplayerSessionNotFoundError(
                f"Multiplayer session with id {session_id} not found"
            )
        return multiplayer_session

    async def save_session(self, multiplayer_session: MultiplayerSession):
        sessions[multiplayer_session.id] = multiplayer_session
