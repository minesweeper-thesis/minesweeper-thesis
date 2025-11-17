import uuid
from typing import ClassVar, Optional, Self

from pydantic import BaseModel, Field, model_validator

from backend.core.board import DifficultyLevel
from backend.core.game import *

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
    def validate(self) -> Self:
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


class GameActionRequest(BaseModel):
    type: ClassVar[str]

    def to_action(self) -> GameAction:
        raise NotImplementedError()


class HintRequest(GameActionRequest):
    type: ClassVar[str] = "hint"

    def to_action(self) -> HintAction:
        return HintAction()


class CellGameActionRequest(GameActionRequest):
    cell: tuple[int, int]


class RevealOneRequest(CellGameActionRequest):
    type: ClassVar[str] = "reveal_one"

    def to_action(self) -> RevealOneAction:
        return RevealOneAction(self.cell)


class RevealManyRequest(CellGameActionRequest):
    type: ClassVar[str] = "reveal_many"

    def to_action(self) -> RevealManyAction:
        return RevealManyAction(self.cell)


class FlagRequest(CellGameActionRequest):
    type: ClassVar[str] = "flag"

    def to_action(self) -> FlagAction:
        return FlagAction(self.cell)


class RemoveFlagRequest(CellGameActionRequest):
    type: ClassVar[str] = "remove_flag"

    def to_action(self) -> RemoveFlagAction:
        return RemoveFlagAction(self.cell)


class GameStateRequest(GameActionRequest):
    type: ClassVar[str] = "get_state"

    def to_action(self) -> GameStateAction:
        return GameStateAction()


def parse_game_action(data: dict) -> GameAction:
    try:
        action_type = data["type"]

        def get_subclassess(cls):
            return set(cls.__subclasses__()) | {
                s for c in cls.__subclasses__() for s in get_subclassess(c)
            }

        model_map: dict[str, type[GameActionRequest]] = {
            subclass.type: subclass
            for subclass in get_subclassess(GameActionRequest)
            if hasattr(subclass, "type")
        }

        return model_map[action_type](**data).to_action()
    except KeyError:
        raise ValueError(f"Unknown action type: {action_type}")


class NewGameResponse(BaseModel):
    gameplay_id: uuid.UUID
    board_id: uuid.UUID
    start_field: tuple[int, int]


class GameActionResponse(ABC, BaseModel):
    type: str

    @staticmethod
    def create(result: ActionResult) -> "GameActionResponse":
        mapping: dict[type[ActionResult], type[GameActionResponse]] = {
            RevealResult: RevealResponse,
            FlagResult: FlagResponse,
            HintResult: HintResponse,
            GameOverResult: GameOverResponse,
            GameStateResult: GameStateResponse,
        }
        return mapping[type(result)]._from_action_result(result)  # type: ignore


class RevealResponse(GameActionResponse):
    type: str = "reveal"
    revealed_cells: list[RevealedCell]
    game_status: GameStatus

    @staticmethod
    def _from_action_result(
        result: RevealResult,
    ) -> "RevealResponse":
        return RevealResponse(
            revealed_cells=result.revealed_cells,
            game_status=result.game_status,
        )


class GameOverResponse(GameActionResponse):
    type: str = "game_over"
    game_status: GameResult
    full_board: list[list[int]]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None

    @staticmethod
    def _from_action_result(
        result: GameOverResult,
    ) -> "GameOverResponse":
        return GameOverResponse(
            game_status=result.result,
            full_board=result.full_board,
            elapsed_time=result.elapsed_time,
            loss_cause=result.loss_cause,
        )


class GameStateResponse(GameActionResponse):
    type: str = "game_state"
    status: GameStatus
    result: Optional[GameResult]
    revealed_cells: list[RevealedCell]
    elapsed_time: float
    loss_cause: Optional[LossCause] = None
    start_field: Cell

    @staticmethod
    def _from_action_result(
        result: GameStateResult,
    ) -> "GameStateResponse":
        return GameStateResponse(
            status=result.status,
            result=result.result,
            revealed_cells=result.revealed_cells,
            elapsed_time=result.elapsed_time,
            loss_cause=result.loss_cause,
            start_field=result.start_field,
        )


class FlagResponse(GameActionResponse):
    type: str = "flag"
    game_status: GameStatus

    @staticmethod
    def _from_action_result(
        result: FlagResult,
    ) -> "FlagResponse":
        return FlagResponse(
            game_status=result.game_status,
        )


class RemoveFlagResponse(GameActionResponse):
    type: str = "remove_flag"
    game_status: GameStatus

    @staticmethod
    def _from_action_result(
        result: FlagResult,
    ) -> "FlagResponse":
        return FlagResponse(
            game_status=result.game_status,
        )


class HintResponse(GameActionResponse):
    type: str = "hint"
    safe_cells: list[Cell]

    @staticmethod
    def _from_action_result(
        result: HintResult,
    ) -> "HintResponse":
        return HintResponse(
            safe_cells=result.safe_cells,
        )
