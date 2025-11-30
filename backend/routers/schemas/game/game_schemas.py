import enum
import uuid
from typing import Literal, Optional, Self

from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.routers.schemas import Response, WSRequest


class HintRequest(WSRequest):
    ws_type: Literal["hint"] = "hint"

    def parse(self) -> HintAction:
        return HintAction()


class CellGameActionRequest(WSRequest):
    cell: tuple[int, int]


class RevealOneRequest(CellGameActionRequest):
    ws_type: Literal["reveal_one"] = "reveal_one"

    def parse(self) -> RevealOneAction:
        return RevealOneAction(self.cell)


class RevealManyRequest(CellGameActionRequest):
    ws_type: Literal["reveal_many"] = "reveal_many"

    def parse(self) -> RevealManyAction:
        return RevealManyAction(self.cell)


class FlagRequest(CellGameActionRequest):
    ws_type: Literal["flag"] = "flag"

    def parse(self) -> FlagAction:
        return FlagAction(self.cell)


class RemoveFlagRequest(CellGameActionRequest):
    ws_type: Literal["remove_flag"] = "remove_flag"

    def parse(self) -> RemoveFlagAction:
        return RemoveFlagAction(self.cell)


class GameStateRequest(WSRequest):
    ws_type: Literal["get_state"] = "get_state"

    def parse(self) -> GameStateAction:
        return GameStateAction()


class RevealResponse(Response):
    ws_type: Literal["reveal"] = "reveal"
    revealed_cells: list[RevealedCell]
    game_status: GameStatus

    @classmethod
    def build(cls, result: RevealResult) -> Self:
        return cls(
            revealed_cells=result.revealed_cells,
            game_status=result.game_status,
        )


class GameOverResponse(Response):
    ws_type: Literal["game_over"] = "game_over"
    game_status: GameResult
    full_board: list[list[int]]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None

    @classmethod
    def build(cls, result: GameOverResult) -> Self:
        return cls(
            game_status=result.result,
            full_board=result.full_board,
            elapsed_time=result.elapsed_time,
            loss_cause=result.loss_cause,
        )


class CellSpecial(enum.Enum):
    START_FIELD = -5
    FLAG = -4
    NOT_REVEALED = -3
    LOSING_MINE = -2


type CellState = CellSpecial | int


class GameStateResponse(Response):
    ws_type: Literal["game_state"] = "game_state"
    board_id: uuid.UUID
    status: GameStatus
    result: Optional[GameResult]
    board: Optional[list[list[CellState]]]
    difficulty_level: DifficultyLevel
    elapsed_time: float
    loss_cause: Optional[LossCause] = None
    start_field: Cell

    @classmethod
    def build(cls, result: GameState) -> Self:
        rows = result.difficulty_level.rows
        cols = result.difficulty_level.columns

        board: list[list[CellState]] = [
            [CellSpecial.NOT_REVEALED for _ in range(cols)] for _ in range(rows)
        ]

        x, y = result.start_field
        board[x][y] = CellSpecial.START_FIELD

        for x, y, val in result.revealed_cells:
            board[x][y] = val

        for x, y in result.flagged_cells:
            board[x][y] = CellSpecial.FLAG

        if result.loss_cause is not None:
            if (
                result.loss_cause.type == "mine_clicked"
                and result.loss_cause.cell is not None
            ):
                mx, my = result.loss_cause.cell
                board[mx][my] = CellSpecial.LOSING_MINE

        return cls(
            board_id=result.board_id,
            status=result.status,
            result=result.result,
            board=board if result.status != "not_started" else None,
            difficulty_level=result.difficulty_level,
            elapsed_time=result.elapsed_time,
            loss_cause=result.loss_cause,
            start_field=result.start_field,
        )


class FlagResponse(Response):
    ws_type: Literal["flag"] = "flag"
    game_status: GameStatus

    @classmethod
    def build(cls, result: FlagResult) -> Self:
        return cls(
            game_status=result.game_status,
        )


class RemoveFlagResponse(Response):
    ws_type: Literal["remove_flag"] = "remove_flag"
    game_status: GameStatus

    @classmethod
    def build(cls, result: RemoveFlagResult) -> Self:
        return cls(
            game_status=result.game_status,
        )


class HintResponse(Response):
    ws_type: Literal["hint"] = "hint"
    safe_cells: list[Cell]

    @classmethod
    def build(cls, result: HintResult) -> Self:
        return cls(
            safe_cells=result.safe_cells,
        )
