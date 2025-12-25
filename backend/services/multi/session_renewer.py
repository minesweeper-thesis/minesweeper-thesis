import logging
import uuid

from backend.core.lobby.create_session import create_session
from backend.di.dependencies import LobbyRepositoryDep, MultiplayerRepositoryDep

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

        existing_session = await self.multi_repo.get_for_lobby(lobby_id)
        if existing_session and not existing_session.is_over():
            logger.debug(f"Session for lobby {lobby_id} exists: {existing_session.id}")
            return

        session = await create_session(lobby)
        await self.multi_repo.save_session(session)

        logger.info(f"Session renewed for lobby {lobby_id}: {session.id}")
