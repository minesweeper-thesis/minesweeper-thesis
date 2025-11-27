import asyncio
import uuid
from typing import Annotated, Optional

from fastapi import BackgroundTasks, Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.board import BoardGenerator, DifficultyLevel, GenerationSettings
from backend.core.game import *
from backend.core.singleplayer import SingleplayerGameplay
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

        if game_settings.generator and game_settings.difficulty_level:
            await pending_store.create_pending(
                gameplay_id=gameplay_id,
                user_id=user.id if user else None,
                ttl_seconds=180,
                settings=GameplaySettings(mode=game_settings.mode),
            )

            def task():
                assert game_settings.generator is not None
                assert game_settings.difficulty_level is not None
                asyncio.run(
                    self._generate(
                        gameplay_id=gameplay_id,
                        difficulty_level=game_settings.difficulty_level,
                        generator_settings=game_settings.generator,
                        pending_store=pending_store,
                    )
                )

            self.background_tasks.add_task(task)

            return gameplay_id

        else:
            board = await self._get_board(game_settings, user)

            gameplay = SingleplayerGameplay(
                id=gameplay_id,
                board=board,
                mode=game_settings.mode,
            )

            await self.game_repo.add_gameplay(
                gameplay, board.id, user.id if user else None
            )

            return gameplay_id

    async def _get_board(
        self, game_settings: NewGameSettings, user: OptionalCurrentUser
    ):
        try:
            if game_settings.board_id:
                board = await self.board_repo.get_board_by_id(game_settings.board_id)

            elif game_settings.difficulty_level:
                board = await self.board_repo.get_unsolved_board(
                    game_settings.difficulty_level, user
                )

            else:
                raise ValueError("Invalid NewGameInput provided")

            return board

        except BoardNotFound:
            raise BoardNotExists(
                f"Board with id {game_settings.board_id} does not exist"
            ) from None

        except UnsolvedBoardNotFound:
            assert game_settings.difficulty_level is not None
            raise SolvedAllBoards(game_settings.difficulty_level) from None

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
