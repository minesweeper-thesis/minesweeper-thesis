import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from algorithms.boards.grid import Grid
from backend import repositories, services
from backend.core.game.game import GameStatus, InvalidAction, SingleplayerGameplay
from backend.models import game_models
from backend.repositories.exceptions import (
    BoardNotFound,
    GameplayNotFound,
    UnsolvedBoardNotFound,
)
from backend.schemas.game_schemas import *
from backend.services.auth_service import CurrentUser, OptionalCurrentUser
from backend.services.exceptions import *

GameRepository = Annotated[repositories.GameRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
BoardService = Annotated[services.BoardService, Depends()]


class RevealResult(BaseModel):
    revealed_cells: list[RevealedCell]
    game_status: Literal["in_progress"] = "in_progress"


class FlagResult(BaseModel):
    game_status: Literal["in_progress"] = "in_progress"


class GameOverResult(BaseModel):
    game_status: Literal["win", "loss"]
    full_board: list[list[int]]
    elapsed_time: float


type ActionResult = RevealResult | FlagResult | GameOverResult

type IsGameOver = bool


class GameService:
    def __init__(
        self,
        board_service: BoardService,
        board_repo: BoardRepository,
        game_repo: GameRepository,
    ):
        self.board_service = board_service
        self.game_repo = game_repo
        self.board_repo = board_repo
        self.gameplay = None
        self.gameplay_id = None
        self.game_over = False

    async def load_gameplay(self, gameplay_id: uuid.UUID):
        try:
            db_gameplay = await self.game_repo.get_gameplay_by_id(gameplay_id)

            if db_gameplay.status == GameStatus.finished:
                raise GameplayAlreadyFinished()

            board = await self.board_repo.get_board_by_id(db_gameplay.board_id)

            grid = Grid(
                rows=board.board_type.rows,
                columns=board.board_type.columns,
                mined_fields=board.minefields,
            )

            self.gameplay = SingleplayerGameplay(
                grid=grid,
                revealed_cells=db_gameplay.revealed_cells,
                elapsed_time=db_gameplay.time,
                used_hints=db_gameplay.used_hints,
                game_status=db_gameplay.status,
                game_result=db_gameplay.result,
            )
            self.gameplay_id = gameplay_id

        except GameplayNotFound:
            raise GameplayNotExists(
                f"Gameplay with id {gameplay_id} does not exist"
            ) from None

    async def create_singleplayer_gameplay(
        self, user: OptionalCurrentUser, new_game_input: NewGameInput
    ) -> NewGameResponse:
        board = await self._get_board(new_game_input, user)

        db_gameplay = game_models.SingleplayerGameplay(
            user_id=user.id if user else None,
            board_id=board.id,
        )
        db_gameplay = await self.game_repo.add_gameplay(db_gameplay)

        return NewGameResponse(
            gameplay_id=db_gameplay.id,
            board_id=board.id,
            start_field=board.start_field,
        )

    async def _get_board(self, new_game_input: NewGameInput, user: OptionalCurrentUser):
        try:
            if new_game_input.board_id:
                board = await self.board_repo.get_board_by_id(new_game_input.board_id)
            elif new_game_input.generator and new_game_input.difficulty_level:
                board = await self.board_service.generate_board(
                    new_game_input.generator,
                    new_game_input.difficulty_level,
                )
            elif new_game_input.difficulty_level:
                board = await self.board_repo.get_unsolved_board(
                    new_game_input.difficulty_level, user
                )
            else:
                raise ValueError("Invalid NewGameInput provided")

            return board

        except BoardNotFound:
            raise BoardNotExists(
                f"Board with id {new_game_input.board_id} does not exist"
            ) from None

        except UnsolvedBoardNotFound:
            assert new_game_input.difficulty_level is not None
            raise SolvedAllBoards(new_game_input.difficulty_level) from None

    async def get_gameplays(self, user: CurrentUser, pagination_params: Params):
        return await self.game_repo.get_gameplays(user.id, pagination_params)

    async def handle_game_action(
        self, action: GameAction
    ) -> tuple[ActionResult, IsGameOver]:
        if self.gameplay is None:
            raise RuntimeError("Gameplay not loaded")

        try:
            actions = {
                RevealOne.type: self._handle_reveal_action,
                RevealMany.type: self._handle_reveal_action,
                Flag.type: self._handle_flag_action,
                RemoveFlag.type: self._handle_flag_action,
                Hint.type: self._handle_hint_action,
            }

            return await actions[action.type](action)
        except:
            raise ValueError(f"Invalid action type: {action.type}")

    async def _handle_hint_action(
        self, action: GameAction
    ) -> tuple[HintResponse, IsGameOver]:
        assert self.gameplay is not None
        safe_cells = self.gameplay.use_hint()

        return HintResponse(safe_cells=safe_cells), False

    async def _handle_reveal_action(
        self, action: CellGameAction
    ) -> tuple[RevealResult | GameOverResult, IsGameOver]:
        assert self.gameplay is not None
        actions = {
            "reveal_one": self.gameplay.reveal_one,
            "reveal_many": self.gameplay.reveal_many,
        }

        x, y = action.cell

        with suppress(InvalidAction):
            result = actions[action.type](x, y)

        if self.gameplay.status == GameStatus.finished:
            assert self.gameplay.elapsed_time is not None
            assert self.gameplay.result is not None

            self.game_over = True
            return (
                GameOverResult(
                    game_status=self.gameplay.result.value,
                    full_board=self.gameplay.grid.grid,
                    elapsed_time=self.gameplay.elapsed_time,
                ),
                True,
            )
        return RevealResult(revealed_cells=result), False

    async def _handle_flag_action(
        self, action: CellGameAction
    ) -> tuple[FlagResult, IsGameOver]:
        assert self.gameplay is not None
        actions = {
            "flag": self.gameplay.flag,
            "remove_flag": self.gameplay.remove_flag,
        }
        x, y = action.cell

        actions[action.type](x, y)

        return FlagResult(), False

    async def save_gameplay_progress(self):
        if self.gameplay is None or self.gameplay_id is None:
            raise RuntimeError("Gameplay not loaded")

        if not self.game_over:
            self.gameplay.update_elapsed_time()

        await self.game_repo.update_gameplay(
            self.gameplay_id,
            status=self.gameplay.status,
            result=self.gameplay.result,
            time=self.gameplay.elapsed_time,
            used_prompts=self.gameplay.used_hints,
            revealed_cells=self.gameplay.get_revealed_cells(),
        )
