from backend.core.user import User
from backend.di.dependencies import (
    LobbyRepositoryDep,
    NotificationSystemDep,
    UserRepositoryDep,
)
from backend.services.dto.lobby import UserCurrentLobby, UserOnlineUpdated
from backend.services.dto.round import UserNotReady, UserReady


class UserConnectionService:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        user_repo: UserRepositoryDep,
        notification_system: NotificationSystemDep,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.notification_system = notification_system

    async def set_user_online(self, user: User):
        await self.user_repo.set_user_online(user.id)

        await self._notify_current_lobby(user)
        await self._notify_user_online_status(user)

    async def set_user_offline(self, user: User):
        await self.user_repo.set_user_offline(user.id)

        await self._notify_user_online_status(user)

    async def _notify_current_lobby(self, user: User):
        lobby = self.lobby_repo.get_user_lobby(user)
        await self.notification_system.notify(user.id, UserCurrentLobby(lobby))

        if lobby:
            for user in lobby.users:
                if lobby.is_user_ready(user):
                    await self.notification_system.notify(
                        user.id, UserReady(user.id, 0)
                    )
                else:
                    await self.notification_system.notify(
                        user.id, UserNotReady(user.id, 0)
                    )

    async def _notify_user_online_status(self, user: User):
        user = await self.user_repo.get_user(user.id)
        user_lobby = self.lobby_repo.get_user_lobby(user)
        if user_lobby:
            data = UserOnlineUpdated(lobby_id=user_lobby.id, user=user)
            for lobby_user in user_lobby.users:
                await self.notification_system.notify(lobby_user.id, data)


__all__ = ["UserConnectionService"]
