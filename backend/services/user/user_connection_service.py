import logging
import uuid
from datetime import datetime, timedelta

from backend.core.lobby import Lobby
from backend.core.user import User
from backend.di.dependencies import *
from backend.services.dto import (
    UserCurrentLobby,
    UserNotReady,
    UserOnlineUpdated,
    UserReady,
)

logger = logging.getLogger(__name__)

REMOVE_OFFLINE_USER_DELAY = timedelta(seconds=10)


class UserConnectionService:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        user_repo: UserRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        notification_system: NotificationSystemDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.multi_repo = multi_repo
        self.notification_system = notification_system
        self.lobby_transport_factory = lobby_transport_factory

    async def broadcast(self, lobby: Lobby, data):
        transport = self.lobby_transport_factory.create(lobby.id)
        for user in lobby.users:
            await transport.send(user.id, data)

    async def send(self, lobby: Lobby, user_id: uuid.UUID, data):
        transport = self.lobby_transport_factory.create(lobby.id)
        await transport.send(user_id, data)

    async def set_user_online(self, user: User):
        await self.user_repo.set_user_online(user.id)

        await self._notify_current_lobby(user)
        await self._notify_user_online_status(user)

    async def set_user_offline(self, user: User):
        await self.user_repo.set_user_offline(user.id)

        await self._notify_user_online_status(user)

    async def _notify_current_lobby(self, user: User):
        lobby = await self.lobby_repo.get_user_lobby(user.id)
        await self.notification_system.notify(user.id, UserCurrentLobby(lobby))

    async def notify_ready_users(self, user: User):
        logger.debug(f"notify_ready_users(user_id={user.id}) called")
        lobby = await self.lobby_repo.get_user_lobby(user.id)
        session = await self.multi_repo.get_for_lobby(lobby.id) if lobby else None
        if lobby is not None and session is not None:
            for user_id in session.player_ids:
                data: UserReady | UserNotReady
                if session.is_user_ready(user_id):
                    data = UserReady(user_id, 0)
                else:
                    data = UserNotReady(user_id, 0)
                await self.send(lobby, user.id, data)

    async def _notify_user_online_status(self, user: User):
        user = await self.user_repo.get_user(user.id)
        user_lobby = await self.lobby_repo.get_user_lobby(user.id)
        if user_lobby:
            data = UserOnlineUpdated(lobby_id=user_lobby.id, user=user)
            await self.broadcast(user_lobby, data)

            if user.is_online:
                kick_at = None
            else:
                kick_at = datetime.now() + REMOVE_OFFLINE_USER_DELAY

            await self.lobby_repo.set_kick_at(user.id, user_lobby.id, kick_at)


__all__ = ["UserConnectionService"]
