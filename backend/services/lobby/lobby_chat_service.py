import logging
import uuid

from fastapi_pagination import Params

logger = logging.getLogger(__name__)

from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.repositories.exceptions import *
from backend.services.exceptions import *
from backend.services.lobby.helpers import *


class LobbyChatService:
    def __init__(
        self, lobby_repo: LobbyRepositoryDep, notification_system: NotificationSystemDep
    ):
        self.lobby_repo = lobby_repo
        self.notification_system = notification_system

    async def send_chat_message(self, lobby_id: uuid.UUID, user: User, content: str):
        logger.debug(
            f"send_chat_message(lobby_id={lobby_id}, user_id={user.id}, content_len={len(content)})"
        )
        lobby = self.lobby_repo.get_lobby(lobby_id)

        ensure_lobby_exists(lobby)
        ensure_user_in_lobby(lobby, user)

        message = LobbyChatMessage(
            lobby_id=lobby_id,
            sender=user,
            content=content,
            timestamp=datetime.now(),
        )

        self.lobby_repo.add_message(message)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, message)

        logger.debug(f"Chat message sent in lobby {lobby_id} by user {user.id}")

    async def get_chat_messages(
        self, lobby_id: uuid.UUID, user: User, pagination_params: Params
    ):
        logger.debug(f"get_chat_messages(lobby_id={lobby_id}, user_id={user.id})")
        lobby = self.lobby_repo.get_lobby(lobby_id)
        ensure_lobby_exists(lobby)
        ensure_user_in_lobby(lobby, user)

        return self.lobby_repo.get_messages(lobby_id, pagination_params)


__all__ = ["LobbyChatService"]
