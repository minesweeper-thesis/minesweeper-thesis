from backend.core.user import User
from backend.di.dependencies import (
    LobbyRepositoryDep,
    MultiplayerRepositoryDep,
    NotificationSystemDep,
    UserRepositoryDep,
)
from backend.services.dto import (
    UserCurrentLobby,
    UserNotReady,
    UserOnlineUpdated,
    UserReady,
)


class UserConnectionService:
    def __init__(
        self,
        lobby_repo: LobbyRepositoryDep,
        user_repo: UserRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        notification_system: NotificationSystemDep,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.multi_repo = multi_repo
        self.notification_system = notification_system

    async def set_user_online(self, user: User):
        await self.user_repo.set_user_online(user.id)

        await self._notify_current_lobby(user)
        await self._notify_user_online_status(user)

    async def set_user_offline(self, user: User):
        await self.user_repo.set_user_offline(user.id)

        await self._notify_user_online_status(user)

    async def _notify_current_lobby(self, user: User):
        lobby = await self.lobby_repo.get_user_lobby(user.id)
        session = (
            await self.multi_repo.get_pending_for_lobby(lobby.id) if lobby else None
        )
        await self.notification_system.notify(user.id, UserCurrentLobby(lobby))

        if session is not None:
            for user_id in session.player_ids:
                if session.is_user_ready(user_id):
                    await self.notification_system.notify(
                        user.id, UserReady(user.id, 0)
                    )
                else:
                    await self.notification_system.notify(
                        user.id, UserNotReady(user.id, 0)
                    )

    async def _notify_user_online_status(self, user: User):
        user = await self.user_repo.get_user(user.id)
        user_lobby = await self.lobby_repo.get_user_lobby(user.id)
        if user_lobby:
            data = UserOnlineUpdated(lobby_id=user_lobby.id, user=user)
            for lobby_user in user_lobby.users:
                await self.notification_system.notify(lobby_user.id, data)


__all__ = ["UserConnectionService"]
