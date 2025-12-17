from typing import Annotated

from fastapi import Depends

from backend.core.board import Board
from backend.core.multi import MultiplayerSession
from backend.di.dependencies import (
    BackgroundRoundHandlerDep,
    BoardGeneratorDep,
    BoardRepositoryDep,
    PendingBoardsStoreDep,
)
from backend.protocols.board_repo_protocol import UnsolvedBoardNotFound
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.services.multi.round_scheduler import RoundScheduler


class SessionBoardsPreparer:
    def __init__(
        self,
        board_repo: BoardRepositoryDep,
        board_generator: BoardGeneratorDep,
        pending_store: PendingBoardsStoreDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
        background_handler: BackgroundRoundHandlerDep,
    ):
        self.board_repo = board_repo
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
            await self.round_scheduler.on_board_generated(session.id, None, board)

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
        game_config = session.game_config
        generation_id = await self.board_generator.generate_board(
            game_config.generation_settings,
            on_completed=lambda generation_id, board: self.background_handler.on_board_generated(
                session.id, generation_id, board
            ),
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
            24 * 3600,
        )


__all__ = ["SessionBoardsPreparer"]
