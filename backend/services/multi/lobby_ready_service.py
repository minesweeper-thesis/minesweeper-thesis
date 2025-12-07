import uuid
from collections.abc import Callable
from typing import Annotated, Any, Awaitable, Optional

from fastapi import Depends

from backend import protocols, repositories
from backend.core.board import Board
from backend.core.game import *
from backend.core.lobby import create_session
from backend.core.lobby.lobby import Lobby
from backend.core.multi.config import GameConfig
from backend.core.multi.session import MultiplayerSession
from backend.core.user import User
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.lib.pending_boards import get_pending_boards_store
from backend.lib.websocket_game_transport import WebSocketGameTransport
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.repositories.exceptions import *
from backend.services.dto import *
from backend.services.dto.round import UserNotReady
from backend.services.exceptions import *
from backend.services.multi.round_scheduler import RoundScheduler

MultiplayerRepository = Annotated[
    protocols.MultiplayerRepository, Depends(repositories.MultiplayerRepository)
]
BoardRepository = Annotated[
    protocols.BoardRepository, Depends(repositories.BoardRepository)
]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
GameTransport = Annotated[
    protocols.GameTransport, Depends(lambda: WebSocketGameTransport())
]
BoardGenerator = Annotated[protocols.BoardGenerator, Depends(LocalBoardGenerator)]
PendingBoardsStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]


type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


class LobbyReadyService:
    def __init__(
        self,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        multi_repo: MultiplayerRepository,
        notification_system: NotificationSystem,
        game_transport: GameTransport,
        board_generator: BoardGenerator,
        pending_store: PendingBoardsStore,
        round_scheduler: Annotated[RoundScheduler, Depends()],
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.notification_system = notification_system
        self.game_transport = game_transport
        self.board_generator = board_generator
        self.pending_store = pending_store

        self.round_scheduler = round_scheduler

    async def _is_session_active(
        self, lobby_session: Optional[MultiplayerSession]
    ) -> bool:
        if lobby_session is None:
            return False

        if len(lobby_session.rounds) == 0:
            return False

        if lobby_session.rounds[0]._state == "not_started":
            return False

        if lobby_session.is_session_over():
            return False

        return True

    async def toggle_user_ready_in_lobby(self, lobby_id: uuid.UUID, user: User):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if lobby.is_user_ready(user):
            await self._cancel_user_ready(lobby, user)
        else:
            await self.set_user_ready_in_lobby(lobby_id, user)

    async def cancel_user_ready_in_lobby(self, lobby_id: uuid.UUID, user: User):
        await self._cancel_user_ready(self.lobby_repo.get_lobby(lobby_id), user)

    async def _cancel_user_ready(self, lobby: Lobby, user: User):
        lobby_session = await self.multi_repo.get_pending_for_lobby(lobby.id)
        if await self._is_session_active(lobby_session):
            return
        if not lobby.is_user_ready(user):
            return
        lobby.set_user_not_ready(user)
        self.lobby_repo.save_lobby(lobby)

        for player in lobby.users:
            await self.notification_system.notify(player.id, UserNotReady(user.id, 0))

    async def set_user_ready_in_lobby(self, lobby_id: uuid.UUID, user: User):
        lobby = self.lobby_repo.get_lobby(lobby_id)

        lobby_session = await self.multi_repo.get_pending_for_lobby(lobby.id)
        if await self._is_session_active(lobby_session):
            return

        if lobby.is_user_ready(user):
            return
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        for player in lobby.users:
            await self.notification_system.notify(player.id, UserReady(user.id, 0))

        if lobby.all_users_ready():
            if lobby_session is not None:
                if lobby_session.game_config == lobby.game_config:
                    session = lobby_session
                else:
                    await self.multi_repo.delete_pending(lobby_session.id)

                    # todo cancel tasks
                    session_id = uuid.uuid4()
                    session = await create_session(session_id, lobby)
            else:
                session_id = uuid.uuid4()
                session = await create_session(session_id, lobby)

            await self.multi_repo.save_pending(session)

            for user_id in session.player_ids:
                await self.notification_system.notify(
                    user_id,
                    RoundReady(session.id, 0, session.game_config.difficulty_level),
                )

            self.lobby = lobby
            self.session = session
            await self._prepare_boards()

    async def _prepare_boards(self):
        to_generate = self.session.rounds_number - len(self.session.rounds)

        for round_index in range(to_generate):
            game_config = self.lobby.game_config
            await self._get_board(game_config, round_index)

    async def _get_board(self, game_config: GameConfig, round_index: int):
        board = await self._get_unsolved_or_generate_board(game_config, round_index)

        if board is not None:
            await self.round_scheduler.on_board_generated(self.session.id, None, board)

    async def _get_unsolved_or_generate_board(
        self, game_config: GameConfig, round_index: int
    ) -> Optional[Board]:
        user_ids = [user.id for user in self.lobby.users]
        try:
            return await self.board_repo.get_unsolved_board(
                game_config.difficulty_level,
                generation_settings=game_config.generation_settings,
                user_ids=user_ids,
            )

        except UnsolvedBoardNotFound:
            await self._generate_board(game_config, round_index)
            return None

    async def _generate_board(self, game_config: GameConfig, round_index: int):
        generation_id = await self.board_generator.generate_board(
            game_config.generation_settings,
            on_completed=lambda generation_id, board: self.round_scheduler.on_board_generated(
                self.session.id, generation_id, board
            ),
        )

        await self.pending_store.create_pending(
            generation_id,
            PendingBoardMetadata(
                generation_settings=game_config.generation_settings,
                difficulty_level=game_config.difficulty_level,
                mode=game_config.game_mode,
                session_id=self.session.id,
                round_index=round_index,
            ),
            24 * 3600,
        )


__all__ = ["LobbyReadyService"]
