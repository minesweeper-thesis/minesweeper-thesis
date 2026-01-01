import logging
from datetime import datetime, timedelta

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
        session_lock: SessionLockDep,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.multi_repo = multi_repo
        self.notification_system = notification_system
        self.lobby_transport_factory = lobby_transport_factory
        self.session_lock = session_lock

    async def set_user_online(self, user: User):
        await self.user_repo.set_user_online(user.id)

        await self._notify_current_lobby(user)
        await self._notify_user_online_status(user)

    async def set_user_offline(self, user: User):
        await self.user_repo.set_user_offline(user.id)

        await self._cancel_user_ready(user)
        await self._notify_user_online_status(user)

    async def _cancel_user_ready(self, user: User):
        logger.debug(f"_cancel_user_ready(user_id={user.id}) called")
        lobby = await self.lobby_repo.get_user_lobby(user.id)
        if lobby is None:
            logger.debug(f"_cancel_user_ready: user {user.id} not in any lobby")
            return

        should_notify = False

        session = await self.multi_repo.get_for_lobby(lobby.id)

        logger.debug(f"_cancel_user_ready: acquiring lock for session {session.id}")
        async with self.session_lock.acquire(session.id):
            session = await self.multi_repo.get_session(session.id)
            assert session is not None, "Session not found"

            is_ready = session.is_user_ready(user.id)
            is_locked = session.ready_locked
            is_started = session.is_started()

            if is_ready and not is_locked and not is_started:
                session.cancel_ready(user.id)
                await self.multi_repo.save_session(session)
                should_notify = True

        if should_notify:
            transport = self.lobby_transport_factory.get(lobby.id)
            next_round_index = session.current_round_index + 1
            await transport.broadcast(UserNotReady(user.id, next_round_index))

    async def _notify_current_lobby(self, user: User):
        lobby = await self.lobby_repo.get_user_lobby(user.id)
        await self.notification_system.notify(user.id, UserCurrentLobby(lobby))

    async def notify_ready_users(self, user: User):
        logger.debug(f"notify_ready_users(user_id={user.id}) called")
        lobby = await self.lobby_repo.get_user_lobby(user.id)
        if lobby is not None:
            session = await self.multi_repo.get_for_lobby(lobby.id)
            transport = self.lobby_transport_factory.get(lobby.id)
            next_round_index = session.current_round_index + 1
            for user_id in session.player_ids:
                if session.is_user_ready(user_id):
                    await transport.send(user.id, UserReady(user_id, next_round_index))
                else:
                    await transport.send(
                        user.id, UserNotReady(user_id, next_round_index)
                    )

    async def _notify_user_online_status(self, user: User):
        logger.debug(f"_notify_user_online_status(user_id={user.id})")
        user = await self.user_repo.get_user(user.id)
        user_lobby = await self.lobby_repo.get_user_lobby(user.id)
        logger.debug(f"User {user.id} is in lobby {user_lobby}")
        if user_lobby:
            data = UserOnlineUpdated(lobby_id=user_lobby.id, user=user)
            transport = self.lobby_transport_factory.get(user_lobby.id)
            await transport.broadcast(data)

            if user.is_online:
                kick_at = None
                logger.debug(f"User {user.id} is online, cancelling scheduled kick")
            else:
                kick_at = datetime.now() + REMOVE_OFFLINE_USER_DELAY
                logger.debug(f"User {user.id} is offline, scheduling kick at {kick_at}")

            await self.lobby_repo.set_kick_at(user.id, user_lobby.id, kick_at)


__all__ = ["UserConnectionService"]
