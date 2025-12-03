import uuid
from typing import Annotated, Optional

from fastapi import Depends

from backend import protocols, repositories
from backend.core.board import Board
from backend.core.game import *
from backend.core.single.gameplay import SingleplayerGameplay
from backend.core.user import User
from backend.lib.auth import OptionalCurrentUser
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.pending_boards import get_pending_boards_store
from backend.protocols.pending_boards import PendingBoardMetadata
from backend.repositories.exceptions import *
from backend.services.dto import *
from backend.services.exceptions import *

SingleplayerRepository = Annotated[
    protocols.SingleplayerRepository, Depends(repositories.SingleplayerRepository)
]
BoardRepository = Annotated[
    protocols.BoardRepository, Depends(repositories.BoardRepository)
]
BoardGenerator = Annotated[protocols.BoardGenerator, Depends(LocalBoardGenerator)]
PendingGameplaysStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]


class CreateSingleplayerGameplayUseCase:
    def __init__(
        self,
        board_repo: BoardRepository,
        game_repo: SingleplayerRepository,
        board_generator: BoardGenerator,
        pending_store: PendingGameplaysStore,
    ):
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.board_generator = board_generator
        self.pending_store = pending_store

    async def create_singleplayer_gameplay(
        self,
        user: OptionalCurrentUser,
        game_settings: NewGameSettings,
    ) -> uuid.UUID:
        gameplay_id = uuid.uuid4()

        board = await self._get_board(gameplay_id, game_settings, user)

        if board is not None:
            await self._create_and_save_gameplay(
                gameplay_id, board, game_settings.mode, user
            )

        return gameplay_id

    async def _get_board(
        self,
        gameplay_id: uuid.UUID,
        game_settings: NewGameSettings,
        user: OptionalCurrentUser,
    ):
        board: Optional[Board] = None

        try:
            if game_settings.board_id:
                board = await self.board_repo.get_board_by_id(game_settings.board_id)

            if game_settings.difficulty_level and not game_settings.generator:
                board = await self.board_repo.get_unsolved_board(
                    game_settings.difficulty_level, user_id=user.id if user else None
                )

            if game_settings.difficulty_level and game_settings.generator:
                if user:
                    board = await self._get_unsolved_or_generate_board(
                        gameplay_id, game_settings, user
                    )
                else:
                    await self._generate_board(
                        gameplay_id=gameplay_id,
                        game_settings=game_settings,
                        user=None,
                    )
                    board = None

            return board

        except BoardNotFound:
            raise BoardNotExists(
                f"Board with id {game_settings.board_id} does not exist"
            ) from None

        except UnsolvedBoardNotFound:
            assert game_settings.difficulty_level is not None
            raise SolvedAllBoards(
                game_settings.difficulty_level, game_settings.generator
            ) from None

    async def _create_and_save_gameplay(
        self, id: uuid.UUID, board: Board, mode: GameMode, user: Optional[User] = None
    ):
        gameplay = SingleplayerGameplay(
            id=id,
            board=board,
            mode=mode,
        )

        await self.game_repo.add_gameplay(gameplay, board.id, user.id if user else None)

    async def _get_unsolved_or_generate_board(
        self,
        gameplay_id: uuid.UUID,
        game_settings: NewGameSettings,
        user: OptionalCurrentUser,
    ) -> Optional[Board]:
        assert game_settings.difficulty_level is not None
        assert game_settings.generator is not None

        try:
            return await self.board_repo.get_unsolved_board(
                game_settings.difficulty_level,
                generation_settings=game_settings.generator,
                user_id=user.id if user else None,
            )

        except UnsolvedBoardNotFound:
            await self._generate_board(
                gameplay_id=gameplay_id,
                game_settings=game_settings,
                user=user,
            )

            return None

    async def _generate_board(
        self,
        gameplay_id: uuid.UUID,
        game_settings: NewGameSettings,
        user: OptionalCurrentUser,
    ):
        assert game_settings.difficulty_level is not None
        assert game_settings.generator is not None

        async def on_board_generated(generation_id: uuid.UUID, board: Board):
            try:
                existing_board = await self.board_repo.get_board(
                    board.difficulty_level, board.minefields
                )
                board = existing_board
            except BoardNotFound:
                await self.board_repo.add_board(board)

            await self.pending_store.mark_ready(generation_id)

        generation_id = await self.board_generator.generate_board(
            game_settings.generator, on_completed=on_board_generated
        )

        await self.pending_store.create_pending(
            generation_id=generation_id,
            metadata=PendingBoardMetadata(
                gameplay_id=gameplay_id,
                generation_settings=game_settings.generator,
                difficulty_level=game_settings.difficulty_level,
                mode=game_settings.mode,
                user_id=user.id if user else None,
            ),
            ttl_seconds=180,
        )


__all__ = ["CreateSingleplayerGameplayUseCase"]
