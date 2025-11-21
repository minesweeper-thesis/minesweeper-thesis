import enum
import uuid
from typing import Annotated, Literal, Optional, Self

from pydantic import BaseModel, Discriminator, Field, Tag, TypeAdapter, model_validator

from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.core.multiplayer import (
    MultiplayerSessionMessage,
    NotReadyMessage,
    ReadyMessage,
)
from backend.services.singleplayer_service import NewGameSettings

from .board_schemas import *


class NewGameRequest(BaseModel):
    board_id: Optional[uuid.UUID] = Field(
        None,
        description="Use existing board (exclusive with generator, difficulty_level)",
    )
    generator: Optional[GenerationRequest] = Field(
        None,
        description="Board generation settings (requires difficulty_level, exclusive with board_id)",
    )
    difficulty_level: Optional[DifficultyLevel] = Field(
        None,
        description="Difficulty for generation (required with generator, exclusive with board_id)",
    )
    mode: GameMode = "normal"

    @model_validator(mode="after")
    def validate_game_settings(self) -> Self:
        board_id = self.board_id
        generator = self.generator
        difficulty_level = self.difficulty_level

        if board_id is not None:
            if generator is not None or difficulty_level is not None:
                raise ValueError(
                    "If board_id is provided, generator and difficulty_level must not be set."
                )
        elif generator is not None:
            if difficulty_level is None:
                raise ValueError(
                    "If generator is provided, difficulty_level must also be set."
                )
        elif difficulty_level is None:
            raise ValueError(
                "You must provide either board_id, difficulty_level, or both generator and difficulty_level."
            )

        return self

    def to_game_settings(self) -> NewGameSettings:
        return NewGameSettings(
            board_id=self.board_id,
            generator=(
                self.generator.to_generation_settings() if self.generator else None
            ),
            difficulty_level=self.difficulty_level,
            mode=self.mode,
        )


class GameActionRequest(ABC, BaseModel):

    @abstractmethod
    def to_core(self) -> GameAction: ...


class HintRequest(GameActionRequest):
    type: Literal["hint"] = "hint"

    def to_core(self) -> HintAction:
        return HintAction()


class CellGameActionRequest(GameActionRequest):
    cell: tuple[int, int]


class RevealOneRequest(CellGameActionRequest):
    type: Literal["reveal_one"] = "reveal_one"

    def to_core(self) -> RevealOneAction:
        return RevealOneAction(self.cell)


class RevealManyRequest(CellGameActionRequest):
    type: Literal["reveal_many"] = "reveal_many"

    def to_core(self) -> RevealManyAction:
        return RevealManyAction(self.cell)


class FlagRequest(CellGameActionRequest):
    type: Literal["flag"] = "flag"

    def to_core(self) -> FlagAction:
        return FlagAction(self.cell)


class RemoveFlagRequest(CellGameActionRequest):
    type: Literal["remove_flag"] = "remove_flag"

    def to_core(self) -> RemoveFlagAction:
        return RemoveFlagAction(self.cell)


class GameStateRequest(GameActionRequest):
    type: Literal["get_state"] = "get_state"

    def to_core(self) -> GameStateAction:
        return GameStateAction()


GameActionUnion = Annotated[
    Annotated[HintRequest, Tag("hint")]
    | Annotated[RevealOneRequest, Tag("reveal_one")]
    | Annotated[RevealManyRequest, Tag("reveal_many")]
    | Annotated[FlagRequest, Tag("flag")]
    | Annotated[RemoveFlagRequest, Tag("remove_flag")]
    | Annotated[GameStateRequest, Tag("get_state")],
    Discriminator("type"),
]


def parse_game_action(data: dict) -> GameAction:

    adapter: TypeAdapter[GameActionUnion] = TypeAdapter(GameActionUnion)
    request = adapter.validate_python(data)
    return request.to_core()


class NewGameResponse(BaseModel):
    gameplay_id: uuid.UUID
    board_id: uuid.UUID
    start_field: tuple[int, int]


class GameActionResponse(ABC, BaseModel):
    type: str

    @classmethod
    @abstractmethod
    def _from_core(cls, result) -> Self:
        """Create response from domain object."""
        ...

    @staticmethod
    def from_core(result: ActionResult) -> "GameActionResponse":
        """Factory method to create appropriate response based on result type."""
        mapping: dict[type[ActionResult], type[GameActionResponse]] = {
            RevealResult: RevealResponse,
            FlagResult: FlagResponse,
            HintResult: HintResponse,
            GameOverResult: GameOverResponse,
            GameStateResult: GameStateResponse,
        }
        response_class = mapping.get(type(result))
        if response_class is None:
            raise ValueError(f"Unknown result type: {type(result)}")
        return response_class._from_core(result)


class RevealResponse(GameActionResponse):
    type: Literal["reveal"] = "reveal"
    revealed_cells: list[RevealedCell]
    game_status: GameStatus

    @classmethod
    def _from_core(cls, result: RevealResult) -> Self:
        return cls(
            revealed_cells=result.revealed_cells,
            game_status=result.game_status,
        )


class GameOverResponse(GameActionResponse):
    type: Literal["game_over"] = "game_over"
    game_status: GameResult
    full_board: list[list[int]]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None

    @classmethod
    def _from_core(cls, result: GameOverResult) -> Self:
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


class GameStateResponse(GameActionResponse):
    type: Literal["game_state"] = "game_state"
    status: GameStatus
    result: Optional[GameResult]
    board: list[list[CellState]]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None
    start_field: Cell

    @classmethod
    def _from_core(cls, result: GameStateResult) -> Self:
        rows = result.difficulty_level.rows
        cols = result.difficulty_level.columns

        board: list[list[CellState]] = [
            [CellSpecial.NOT_REVEALED for _ in range(cols)] for _ in range(rows)
        ]

        x, y = result.start_field
        board[x][y] = CellSpecial.START_FIELD

        for x, y, val in result.revealed_cells:
            board[x][y] = val

        for x, y in result.flagged:
            board[x][y] = CellSpecial.FLAG

        if result.loss_cause is not None:
            if result.loss_cause.type == "mine_clicked":
                mx, my = result.loss_cause.cell
                board[mx][my] = CellSpecial.LOSING_MINE

        return cls(
            status=result.status,
            result=result.result,
            board=board,
            elapsed_time=result.elapsed_time,
            loss_cause=result.loss_cause,
            start_field=result.start_field,
        )


class FlagResponse(GameActionResponse):
    type: Literal["flag"] = "flag"
    game_status: GameStatus

    @classmethod
    def _from_core(cls, result: FlagResult) -> Self:
        return cls(
            game_status=result.game_status,
        )


class RemoveFlagResponse(GameActionResponse):
    type: Literal["remove_flag"] = "remove_flag"
    game_status: GameStatus

    @classmethod
    def _from_core(cls, result: FlagResult) -> Self:
        return cls(
            game_status=result.game_status,
        )


class HintResponse(GameActionResponse):
    type: Literal["hint"] = "hint"
    safe_cells: list[Cell]

    @classmethod
    def _from_core(cls, result: HintResult) -> Self:
        return cls(
            safe_cells=result.safe_cells,
        )


class MultiplayerSessionMessageRequest(ABC, BaseModel):
    @abstractmethod
    def to_core(self) -> MultiplayerSessionMessage: ...


class ReadyRequest(MultiplayerSessionMessageRequest):
    type: Literal["ready"] = "ready"

    def to_core(self) -> "ReadyMessage":
        return ReadyMessage()


class NotReadyRequest(MultiplayerSessionMessageRequest):
    type: Literal["not_ready"] = "not_ready"

    def to_core(self) -> "NotReadyMessage":
        return NotReadyMessage()


MultiplayerSessionMessageUnion = Annotated[
    Annotated[ReadyRequest, Tag("ready")]
    | Annotated[NotReadyRequest, Tag("not_ready")],
    Discriminator("type"),
]


def parse_multiplayer_session_message(data: dict) -> MultiplayerSessionMessage:
    adapter: TypeAdapter[MultiplayerSessionMessageUnion] = TypeAdapter(
        MultiplayerSessionMessageUnion
    )
    request = adapter.validate_python(data)
    return request.to_core()


class RoundStartResponse(BaseModel):
    type: str = "round_start"
    start_at: int
    end_at: int


class RoundEndResponse(BaseModel):
    type: str = "round_end"


class SessionEndResponse(BaseModel):
    type: str = "session_end"


class FirstRoundStartResponse(RoundStartResponse):
    gameplay_id: uuid.UUID
