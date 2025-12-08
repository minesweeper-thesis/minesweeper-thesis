import logging
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

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
        logger.debug(f"get_session(session_id={session_id})")
        pending = pending_sessions.get(session_id, None)
        multiplayer_session = sessions.get(session_id, pending)
        if not multiplayer_session:
            logger.warning(f"Multiplayer session {session_id} not found")
            raise MultiplayerSessionNotFoundError(
                f"Multiplayer session with id {session_id} not found"
            )
        logger.debug(f"Retrieved multiplayer session {session_id}")
        return multiplayer_session

    async def save_session(self, session: MultiplayerSession):
        logger.debug(f"save_session(session_id={session.id})")
        sessions[session.id] = session
        logger.info(f"Multiplayer session {session.id} saved")

    async def save_pending(self, session: MultiplayerSession):
        logger.debug(
            f"save_pending(session_id={session.id}, lobby_id={session.lobby_id})"
        )
        pending_sessions[session.id] = session
        logger.info(
            f"Pending multiplayer session {session.id} saved for lobby {session.lobby_id}"
        )

    async def is_pending(self, session_id: uuid.UUID) -> bool:
        logger.debug(f"is_pending(session_id={session_id})")
        return session_id in pending_sessions

    async def get_pending_for_lobby(
        self, lobby_id: uuid.UUID
    ) -> Optional[MultiplayerSession]:
        logger.debug(f"get_pending_for_lobby(lobby_id={lobby_id})")
        for session in pending_sessions.values():
            if session.lobby_id == lobby_id:
                return session
        return None

    async def delete_pending(self, session_id: uuid.UUID):
        logger.debug(f"delete_pending(session_id={session_id})")
        pending_sessions.pop(session_id, None)
