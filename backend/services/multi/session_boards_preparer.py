import logging
import uuid
from typing import Annotated

logger = logging.getLogger(__name__)


from fastapi import Depends

from backend.core.board import Board
from backend.core.multi import MultiplayerSession
from backend.di.dependencies import *
from backend.protocols.board_repo_protocol import UnsolvedBoardNotFound
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.services.multi.round_scheduler import RoundScheduler


class SessionBoardsPreparer:
    def __init__(
        self,
        board_repo: BoardRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        board_generator: BoardGeneratorDep,
        pending_store: PendingBoardsStoreDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
        background_handler: BackgroundRoundHandlerDep,
    ):
        self.board_repo = board_repo
        self.multi_repo = multi_repo
        self.board_generator = board_generator
        self.pending_store = pending_store
        self.round_scheduler = round_scheduler
        self.background_handler = background_handler

    async def prepare(self, session: MultiplayerSession):
        to_generate = session.rounds_number - len(session.rounds)

        for round_index in range(to_generate):
            await self._prepare_round_board(session, round_index)

    async def _prepare_round_board(
        self,
        session: MultiplayerSession,
        round_index: int,
    ):
        board = await self._get_unsolved_or_generate_board(session, round_index)

        if board is not None:
            await self.background_handler.on_board_generated(session.id, None, board)

    async def _get_unsolved_or_generate_board(
        self,
        session: MultiplayerSession,
        round_index: int,
    ) -> Board | None:
        try:
            return await self.board_repo.get_unsolved_board(
                session.game_config.difficulty_level,
                generation_settings=session.game_config.generation_settings,
                user_ids=session.player_ids,
            )
        except UnsolvedBoardNotFound:
            await self._generate_board(session, round_index)
            return None

    async def _generate_board(self, session: MultiplayerSession, round_index: int):
        async def on_completed(generation_id: uuid.UUID, board: Board):
            await self.background_handler.on_board_generated(
                session.id, generation_id, board
            )

        game_config = session.game_config
        generation_id = await self.board_generator.generate_board(
            game_config.generation_settings, on_completed=on_completed
        )

        await self.pending_store.create_pending(
            generation_id,
            PendingBoardMetadata(
                generation_settings=game_config.generation_settings,
                difficulty_level=game_config.difficulty_level,
                mode=game_config.game_mode,
                session_id=session.id,
                round_index=round_index,
            ),
        )

    async def wait_and_schedule_next_round(self, session_id: uuid.UUID):
        logger.debug(f"Waiting for pending boards to be ready in session {session_id}")
        session = await self.multi_repo.get_session(session_id)
        next_round_index = session.current_round_index + 1

        pending = await self.pending_store.get_pending_round(
            session.id, next_round_index
        )
        if pending is None:
            raise RuntimeError("Pending board not found")

        await self.pending_store.wait_for_ready(pending.generation_id)

        fresh_session = await self.multi_repo.get_session(session_id)
        await self.round_scheduler.schedule_start(fresh_session)


__all__ = ["SessionBoardsPreparer"]
