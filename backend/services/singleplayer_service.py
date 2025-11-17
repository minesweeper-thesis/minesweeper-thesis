import uuid
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories
from backend.core.board import BoardGenerator
from backend.core.game import *
from backend.core.singleplayer import SingleplayerGameplay
from backend.lib.auth import CurrentUser, OptionalCurrentUser
from backend.repositories.exceptions import *
from backend.services.exceptions import *

SingleplayerRepository = Annotated[repositories.SingleplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]


class SingleplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        game_repo: SingleplayerRepository,
    ):
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.gameplay = None
        self.gameplay_id = None
        self.game_over = False

    async def load_gameplay(self, gameplay_id: uuid.UUID):
        try:
            gameplay = await self.game_repo.get_gameplay_by_id(gameplay_id)

            if gameplay.status == "finished":
                raise GameplayAlreadyFinished()

            self.gameplay = gameplay

        except GameplayNotFound:
            raise GameplayNotExists(
                f"Gameplay with id {gameplay_id} does not exist"
            ) from None

    async def create_singleplayer_gameplay(
        self, user: OptionalCurrentUser, game_settings: NewGameSettings
    ):
        board = await self._get_board(game_settings, user)

        gameplay = SingleplayerGameplay(
            id=uuid.uuid4(),
            board=board,
            mode=game_settings.mode,
        )

        await self.game_repo.add_gameplay(gameplay, board.id, user.id if user else None)

        return gameplay, board

    async def _get_board(
        self, game_settings: NewGameSettings, user: OptionalCurrentUser
    ):
        try:
            if game_settings.board_id:
                board = await self.board_repo.get_board_by_id(game_settings.board_id)

            elif game_settings.generator and game_settings.difficulty_level:
                generator = BoardGenerator(
                    game_settings.difficulty_level,
                    game_settings.generator.type,
                    game_settings.generator.settings,
                )
                board = await generator.generate_board()
                await self.board_repo.add_board(board)

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

    async def handle_game_action(
        self, action: GameAction
    ) -> tuple[Optional[ActionResult], IsGameOver]:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        try:
            return action.handle(self.gameplay)
        except InvalidAction:
            return None, self.gameplay.is_game_over()

    async def get_game_state(self) -> GameStateResult:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        return self.gameplay.get_game_state()

    async def save_gameplay_progress(self):
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        if not self.game_over:
            self.gameplay.update_elapsed_time()

        await self.game_repo.update_gameplay(
            self.gameplay.id,
            status=self.gameplay.status,
            result=self.gameplay.result,
            time=self.gameplay.elapsed_time,
            used_prompts=self.gameplay.used_hints,
            revealed_cells=self.gameplay.get_revealed_cells(),
        )
