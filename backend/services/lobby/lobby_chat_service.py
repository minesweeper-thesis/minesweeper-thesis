import uuid
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import User
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.repositories.exceptions import *
from backend.services.exceptions import *
from backend.services.lobby.helpers import *

LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]


class LobbyChatService:
    def __init__(
        self, lobby_repo: LobbyRepository, notification_system: NotificationSystem
    ):
        self.lobby_repo = lobby_repo
        self.notification_system = notification_system

    async def send_chat_message(self, lobby_id: uuid.UUID, user: User, content: str):
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

    async def get_chat_messages(
        self, lobby_id: uuid.UUID, user: User, pagination_params: Params
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        ensure_lobby_exists(lobby)
        ensure_user_in_lobby(lobby, user)

        return self.lobby_repo.get_messages(lobby_id, pagination_params)


__all__ = ["LobbyChatService"]
