import logging
import uuid
from typing import Annotated, Optional

from fastapi import Depends

logger = logging.getLogger(__name__)

from backend.core.board import Board
from backend.core.game import *
from backend.core.lobby import Lobby, create_session
from backend.core.multi import GameConfig, MultiplayerSession
from backend.core.user import User
from backend.di.dependencies import *
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.repositories.exceptions import *
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.multi.helpers import (
    send_round_ready,
    send_user_not_ready,
    send_user_ready_in_lobby,
)
from backend.services.multi.round_scheduler import RoundScheduler


class LobbyReadyService:
    def __init__(
        self,
        board_repo: BoardRepositoryDep,
        lobby_repo: LobbyRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        notification_system: NotificationSystemDep,
        board_generator: BoardGeneratorDep,
        pending_store: PendingBoardsStoreDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.notification_system = notification_system
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
        logger.debug(f"User {user.id} toggling ready in lobby {lobby_id}")
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

        assert lobby_session is not None
        await send_user_not_ready(self.notification_system.notify, lobby_session, user)

    async def set_user_ready_in_lobby(self, lobby_id: uuid.UUID, user: User):
        lobby = self.lobby_repo.get_lobby(lobby_id)

        lobby_session = await self.multi_repo.get_pending_for_lobby(lobby.id)
        if await self._is_session_active(lobby_session):
            return

        if lobby.is_user_ready(user):
            return
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        await send_user_ready_in_lobby(self.notification_system.notify, lobby, user)

        if lobby.all_users_ready():
            logger.info(f"All users ready in lobby {lobby_id}, creating session")
            session = await self._get_session(lobby, lobby_session)
            await self.multi_repo.save_pending(session)

            await send_round_ready(self.notification_system.notify, session)

            self.lobby = lobby
            self.session = session
            await self._prepare_boards()

    async def _get_session(
        self, lobby: Lobby, lobby_session: Optional[MultiplayerSession]
    ) -> MultiplayerSession:
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

        return session

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
