import asyncio
import uuid
from typing import Annotated, Optional

from fastapi import BackgroundTasks, Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.board import (
    Board,
    BoardGenerator,
    DifficultyLevel,
    GenerationSettings,
)
from backend.core.game import *
from backend.core.singleplayer import SingleplayerGameplay
from backend.core.user import User
from backend.lib.auth import CurrentUser, OptionalCurrentUser
from backend.lib.pending_gameplays import GameplaySettings, PendingStore, pending_store
from backend.repositories.exceptions import *
from backend.services.exceptions import *

SingleplayerRepository = Annotated[repositories.SingleplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]


@dataclass
class NewGameSettings:
    board_id: Optional[uuid.UUID]
    generator: Optional[GenerationSettings]
    difficulty_level: Optional[DifficultyLevel]
    mode: GameMode


class GenerationTimeout(Exception):
    pass


class SingleplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        game_repo: SingleplayerRepository,
        background_tasks: BackgroundTasks,
    ):
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.gameplay: Optional[SingleplayerGameplay] = None
        self.gameplay_id: uuid.UUID = None  # type: ignore
        self.background_tasks: BackgroundTasks = background_tasks

    async def load_gameplay(
        self, gameplay_id: uuid.UUID, timeout: float = 120.0
    ) -> GameStateResult:
        self.gameplay_id = gameplay_id

        if await pending_store.is_pending(gameplay_id):
            pending = await pending_store.wait_for_ready(gameplay_id, timeout=timeout)
            if pending is None or pending.board_id is None:
                raise GenerationTimeout()

            board = await self.board_repo.get_board_by_id(pending.board_id)

            gameplay = SingleplayerGameplay(
                id=gameplay_id,
                board=board,
                mode=pending.settings.mode,
            )
            await self.game_repo.add_gameplay(gameplay, board.id, pending.user_id)

        try:
            await self._set_gameplay(gameplay_id)
            assert self.gameplay is not None

            if self.gameplay.status == "finished":
                raise GameplayAlreadyFinished()

            return self.gameplay.get_game_state()

        except GameplayNotFound:
            raise GameplayNotExists(
                f"Gameplay with id {gameplay_id} does not exist"
            ) from None

    async def _set_gameplay(self, gameplay_id: uuid.UUID):
        gameplay = await self.game_repo.get_gameplay_by_id(gameplay_id)
        self.gameplay = gameplay

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
                    game_settings.difficulty_level, user=user
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
                user=user,
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

        await pending_store.create_pending(
            gameplay_id=gameplay_id,
            user_id=user.id if user else None,
            ttl_seconds=180,
            settings=GameplaySettings(mode=game_settings.mode),
        )

        self._add_generation_task(
            gameplay_id=gameplay_id,
            difficulty_level=game_settings.difficulty_level,
            generator_settings=game_settings.generator,
        )

    async def get_gameplays(self, user: CurrentUser, pagination_params: Params):
        return await self.game_repo.get_gameplays(user.id, pagination_params)

    async def handle_game_action(self, action: GameAction) -> Optional[ActionResult]:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        try:
            return action.handle(self.gameplay)
        except InvalidAction:
            return None

    async def get_game_state(self) -> GameStateResult:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        return self.gameplay.get_game_state()

    async def is_game_over(self) -> bool:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        return self.gameplay.is_game_over()

    async def save_gameplay_progress(self):
        if self.gameplay is None:
            return

        if self.gameplay.status == "in_progress":
            self.gameplay.update_elapsed_time()

        await self.game_repo.update_gameplay(self.gameplay)

    def _add_generation_task(
        self,
        gameplay_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        generator_settings: GenerationSettings,
    ) -> None:
        def task():
            asyncio.run(
                self._generate(
                    gameplay_id=gameplay_id,
                    difficulty_level=difficulty_level,
                    generator_settings=generator_settings,
                    pending_store=pending_store,
                )
            )

        self.background_tasks.add_task(task)

    async def _generate(
        self,
        gameplay_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        generator_settings: GenerationSettings,
        pending_store: PendingStore,
    ) -> None:
        generator = BoardGenerator(
            difficulty_level,
            generator_settings.type,
            generator_settings.settings,
        )
        board = await generator.generate_board()

        try:
            existing_board = await self.board_repo.get_board(
                board.difficulty_level, board.minefields
            )
            board = existing_board
        except BoardNotFound:
            await self.board_repo.add_board(board)

        await pending_store.mark_ready(gameplay_id, board.id)
