import asyncio
import uuid
from typing import Annotated, Awaitable, Callable, Optional

from fastapi import BackgroundTasks, Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.board import BoardGenerator, DifficultyLevel, GenerationSettings
from backend.core.game import *
from backend.core.pending_gameplays import pending_store
from backend.core.singleplayer import SingleplayerGameplay
from backend.lib.auth import CurrentUser, OptionalCurrentUser
from backend.lib.event_bus import event_bus
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


type Callback = Callable[[], Awaitable[None]]


class SingleplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        game_repo: SingleplayerRepository,
        background_tasks: BackgroundTasks,
    ):
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.background_tasks = background_tasks
        self.gameplay: Optional[SingleplayerGameplay] = None
        self.gameplay_id: uuid.UUID = None  # type: ignore
        self.board_ready_callback: Optional[Callback] = None

    async def load_gameplay(self, gameplay_id: uuid.UUID):
        pending = pending_store.get(gameplay_id)
        if pending:
            self.gameplay_id = gameplay_id
            self.gameplay = None
            return

        try:
            await self._set_gameplay(gameplay_id)
            assert self.gameplay is not None

            if self.gameplay.status == "finished":
                raise GameplayAlreadyFinished()

            self.gameplay_id = gameplay_id

        except GameplayNotFound:
            raise GameplayNotExists(
                f"Gameplay with id {gameplay_id} does not exist"
            ) from None

    async def _set_gameplay(self, gameplay_id: uuid.UUID):
        gameplay = await self.game_repo.get_gameplay_by_id(gameplay_id)
        self.gameplay = gameplay

    async def on_board_ready(self):
        await self._set_gameplay(self.gameplay_id)
        assert self.gameplay is not None
        if self.board_ready_callback:
            await self.board_ready_callback()

    async def send_board(self):
        pending = pending_store.get(self.gameplay_id)
        if pending and pending.status == "ready":
            pending_store.remove(self.gameplay_id)
            await self.on_board_ready()
        elif pending:
            await event_bus.subscribe(
                f"board_ready:{self.gameplay_id}", self.on_board_ready
            )
        elif self.gameplay is not None:
            await self.on_board_ready()

    async def create_singleplayer_gameplay(
        self,
        user: OptionalCurrentUser,
        game_settings: NewGameSettings,
    ) -> uuid.UUID:
        gameplay_id = uuid.uuid4()

        if game_settings.generator and game_settings.difficulty_level:
            pending_store.add(gameplay_id)

            self.background_tasks.add_task(
                self._generate_and_save_board,
                gameplay_id,
                user.id if user else None,
                game_settings,
            )

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

    def _generate_and_save_board(
        self,
        gameplay_id: uuid.UUID,
        user_id: Optional[uuid.UUID],
        game_settings: NewGameSettings,
    ) -> None:
        if not game_settings.difficulty_level or not game_settings.generator:
            return

        generator = BoardGenerator(
            game_settings.difficulty_level,
            game_settings.generator.type,
            game_settings.generator.settings,
        )
        board = asyncio.run(generator.generate_board())

        async def _save_to_db():
            await self.board_repo.add_board(board)

            gameplay = SingleplayerGameplay(
                id=gameplay_id,
                board=board,
                mode=game_settings.mode,
            )

            await self.game_repo.add_gameplay(gameplay, board.id, user_id)

            pending_store.mark_ready(gameplay_id)
            await event_bus.publish(
                f"board_ready:{gameplay_id}",
                {"gameplay_id": str(gameplay_id)},
            )

        asyncio.run(_save_to_db())

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

        await self.game_repo.update_gameplay(
            self.gameplay.id,
            status=self.gameplay.status,
            result=self.gameplay.result,
            time=self.gameplay.elapsed_time,
            used_prompts=self.gameplay.used_hints,
            revealed_cells=self.gameplay.get_revealed_cells(),
        )

    async def game_cleanup(self):
        if self.gameplay_id is not None:
            await event_bus.unsubscribe(f"board_ready:{self.gameplay_id}")
            pending_store.remove(self.gameplay_id)
