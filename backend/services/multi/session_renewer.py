import logging
import uuid
from contextlib import suppress

from backend.core.lobby.create_session import create_session
from backend.di.dependencies import LobbyRepositoryDep, MultiplayerRepositoryDep
from backend.protocols.repos.exceptions import SessionNotFound

logger = logging.getLogger(__name__)


class SessionRenewer:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
    ):
        self.lobby_repo = lobby_repo
        self.multi_repo = multi_repo

    async def renew_session(self, lobby_id: uuid.UUID):
        logger.debug(f"renew_session(lobby_id={lobby_id})")
        lobby = await self.lobby_repo.get_lobby(lobby_id)

        with suppress(SessionNotFound):
            existing_session = await self.multi_repo.get_for_lobby(lobby_id)
            if existing_session.is_active():
                logger.info(
                    f"Session for lobby {lobby_id} is still active: {existing_session.id}"
                )
                return

        session = await create_session(lobby)
        await self.multi_repo.save_session(session)

        logger.info(f"Session renewed for lobby {lobby_id}: {session.id}")
