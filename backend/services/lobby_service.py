import asyncio
import time
import uuid
from typing import Annotated, Any, Awaitable, Callable

from fastapi import BackgroundTasks, Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core import lobby
from backend.core.game import *
from backend.core.lobby import *
from backend.core.multi import ROUND_START_DELAY
from backend.core.multi.session import create_multiplayer_session
from backend.core.user import User
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.pending_sessions import pending_sessions_store
from backend.repositories.exceptions import *
from backend.services.exceptions import *


@dataclass
class InvitationsQuery:
    pass


LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]
UserRepository = Annotated[repositories.UserRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends()]

type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


class LobbyService:
    def __init__(
        self,
        lobby_repo: LobbyRepository,
        user_repo: UserRepository,
        board_repo: BoardRepository,
        multi_repo: MultiplayerRepository,
        notification_system: NotificationSystem,
        background_tasks: BackgroundTasks,
    ):
        self.lobby_repo = lobby_repo
        self.user_repo = user_repo
        self.board_repo = board_repo
        self.multi_repo = multi_repo
        self.notification_system = notification_system
        self.background_tasks = background_tasks
        self.task = None

        self.on_session_end_callback: Optional[Callable[[], Awaitable[None]]] = None

    async def create_lobby(self, user: User) -> Lobby:
        default_game_config = GameConfig(
            rounds=3,
            max_round_time=60,
            difficulty_level=DifficultyLevel(3, 3, 3),
            game_mode="normal",
            generator_type="random",
            generator_settings=None,
        )

        lobby = Lobby(id=uuid.uuid4(), host=user, game_config=default_game_config)
        self.lobby_repo.save_lobby(lobby)
        return lobby

    async def get_user_lobby(self, user: User) -> Optional[Lobby]:
        if lobbies := self.lobby_repo.get_user_lobbies(user):
            return lobbies[0]
        return None

    async def join_lobby(
        self,
        user: User,
        invitation_id: uuid.UUID,
    ):
        user_lobbies = self.lobby_repo.get_user_lobbies(user)
        if user_lobbies:
            raise ValueError("User is already in a lobby")

        invitation = self.lobby_repo.get_invitation(invitation_id)
        lobby = invitation.lobby

        if invitation.invitee != user or invitation.lobby != lobby:
            raise PermissionError("User not authorized to join this lobby")

        data = lobby.add_user(user)
        self.lobby_repo.save_lobby(lobby)
        self.lobby_repo.delete_invitation(invitation.id)

        response = InvitationAnswer(invitation=invitation, answer="accepted")
        await self.notification_system.notify(invitation.inviter.id, response)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, data)

        messages = self.lobby_repo.get_messages(lobby.id, Params(page=1, size=10))

        return lobby, messages

    async def update_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
        game_config: GameConfig,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        if lobby.host != user:
            raise PermissionError("User not authorized to update lobby")

        event = lobby.update_game_config(game_config)

        self.lobby_repo.save_lobby(lobby)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, event)

    async def invite_to_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
        invitee_id: uuid.UUID,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        if lobby.host != user:
            raise PermissionError("User not authorized to invite")

        invitee = await self.user_repo.get_user(invitee_id)
        if not invitee:
            raise ValueError("Invitee not found")

        invitation = Invitation(
            id=uuid.uuid4(),
            lobby=lobby,
            inviter=user,
            invitee=invitee,
        )
        await self.notification_system.notify(invitation.invitee.id, invitation)
        self.lobby_repo.save_invitation(invitation)

    async def reject_game_invitation(
        self,
        invitation_id: uuid.UUID,
        user: User,
    ):
        invitation = self.lobby_repo.get_invitation(invitation_id)
        if not invitation:
            raise ValueError("Invitation not found")

        if invitation.invitee != user:
            raise PermissionError("User not authorized to reject this invitation")

        response = InvitationAnswer(invitation=invitation, answer="rejected")
        await self.notification_system.notify(invitation.inviter.id, response)
        self.lobby_repo.delete_invitation(invitation.id)

    async def remove_user_from_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        data = lobby.remove_user(user)

        if lobby.is_empty():
            self.lobby_repo.delete_lobby(lobby_id)
        else:
            self.lobby_repo.save_lobby(lobby)
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, data)

    def _create_game_session(
        self,
        session_id: uuid.UUID,
        lobby_id: uuid.UUID,
        start_at: int,
        game_notify: Notify,
    ):
        current = time.time()
        diff = start_at - current
        time.sleep(diff)

        lobby = self.lobby_repo.get_lobby(lobby_id)
        if lobby.all_users_ready():
            for user in lobby.users:
                lobby.set_user_not_ready(user)
            session = asyncio.run(
                create_multiplayer_session(
                    session_id,
                    lobby.game_config,
                    [user.id for user in lobby.users],
                )
            )

            end_at = start_at + session.max_round_time
            data = session.start_next_round(start_at, end_at)

            asyncio.run(self.multi_repo.save_session(session))

            pending_sessions_store.mark_ready(session_id)

            async def send_start():
                for user_id in session.player_ids:
                    print(f"[LOG] Sending round start to user {user_id}")
                    print(game_notify)
                    await game_notify(user_id, data)

            asyncio.run(send_start())

            self.session_id = session_id
            self.background_tasks.add_task(
                self._schedule_end_round, game_notify=game_notify, end_at=end_at
            )
        else:
            pending_sessions_store.remove(session_id)

    async def _end_round(self, game_notify: Notify):
        session = await self.multi_repo.get_session(self.session_id)
        data = session.end_current_round()
        await self.multi_repo.save_session(session)

        for user_id in session.player_ids:
            await game_notify(user_id, data)

        if session.is_session_over() and self.on_session_end_callback:
            await self.on_session_end_callback()

    def _schedule_end_round(self, end_at: int, game_notify: Notify):
        delay = end_at - int(time.time())
        if delay > 0:
            time.sleep(delay)
        asyncio.run(self._end_round(game_notify))

    async def set_user_ready(
        self,
        lobby_id: uuid.UUID,
        user: User,
        game_notify: Notify,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        if lobby.all_users_ready():
            start_at = int(time.time()) + ROUND_START_DELAY

            session_id = uuid.uuid4()
            pending_sessions_store.add(session_id)

            self.background_tasks.add_task(
                self._create_game_session,
                session_id,
                lobby.id,
                start_at,
                game_notify=game_notify,
            )

            event = lobby.start_countdown(start_at)
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, event)

    async def send_chat_message(
        self,
        lobby_id: uuid.UUID,
        user: User,
        content: str,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        if user not in lobby.users:
            raise PermissionError("User not in the lobby")

        message = ChatMessage(
            lobby_id=lobby_id,
            sender=user,
            content=content,
            timestamp=int(time.time()),
        )

        self.lobby_repo.add_message(message)

        for lobby_user in lobby.users:
            await self.notification_system.notify(lobby_user.id, message)

    async def get_chat_messages(
        self,
        lobby_id: uuid.UUID,
        user: User,
        pagination_params: Params,
    ) -> list[lobby.ChatMessage]:
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if not lobby:
            raise ValueError("Lobby not found")

        if user not in lobby.users:
            raise PermissionError("User not in the lobby")

        return self.lobby_repo.get_messages(lobby_id, pagination_params)

    async def get_pending_invitations(
        self,
        user: User,
    ) -> list[Invitation]:
        return self.lobby_repo.get_pending_invitations(user)
