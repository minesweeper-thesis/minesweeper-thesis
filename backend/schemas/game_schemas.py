import uuid
from typing import ClassVar, Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator

from backend.schemas.board_schemas import *


class NewGameInput(BaseModel):
    board_id: Optional[uuid.UUID] = Field(
        None,
        description="Use existing board (exclusive with generation_settings, difficulty_level)",
    )
    generator: Optional[GenerationInput] = Field(
        None,
        description="Board generation settings (requires difficulty_level, exclusive with board_id)",
    )
    difficulty_level: Optional[DifficultyLevel] = Field(
        None,
        description="Difficulty for generation (required with generation_settings, exclusive with board_id)",
    )

    @model_validator(mode="after")
    def validate(self) -> Self:
        board_id = self.board_id
        generation_settings = self.generator
        difficulty_level = self.difficulty_level

        if board_id is not None:
            if generation_settings is not None or difficulty_level is not None:
                raise ValueError(
                    "If board_id is provided, generation_settings and difficulty_level must not be set."
                )
        elif generation_settings is not None:
            if difficulty_level is None:
                raise ValueError(
                    "If generation_settings is provided, difficulty_level must also be set."
                )
        elif difficulty_level is None:
            raise ValueError(
                "You must provide either board_id, difficulty_level, or both generation_settings and difficulty_level."
            )

        return self


class GameAction(BaseModel):
    type: ClassVar[str]


class Hint(GameAction):
    type: ClassVar[str] = "hint"


class CellGameAction(GameAction):
    cell: tuple[int, int]


class RevealOne(CellGameAction):
    type: ClassVar[str] = "reveal_one"


class RevealMany(CellGameAction):
    type: ClassVar[str] = "reveal_many"


class Flag(CellGameAction):
    type: ClassVar[str] = "flag"


class RemoveFlag(CellGameAction):
    type: ClassVar[str] = "remove_flag"


def parse_game_action(data: dict) -> GameAction:
    try:
        action_type = data["type"]

        def get_subclassess(cls):
            return set(cls.__subclasses__()) | {
                s for c in cls.__subclasses__() for s in get_subclassess(c)
            }

        model_map = {
            subclass.type: subclass
            for subclass in get_subclassess(GameAction)
            if hasattr(subclass, "type")
        }

        return model_map[action_type](**data)
    except KeyError:
        raise ValueError(f"Unknown action type: {action_type}")


type GameState = Literal["in_progress", "won", "lost"]


type Cell = tuple[int, int]
type RevealedCell = tuple[int, int, int]


class NewGameResponse(BaseModel):
    gameplay_id: uuid.UUID
    board_id: uuid.UUID
    start_field: Optional[tuple[int, int]] = None


class GameActionResponse(BaseModel):
    pass


class RevealResponse(GameActionResponse):
    revealed_cells: list[RevealedCell]
    game_state: GameState
    full_board: Optional[list[list[int]]] = None


class FlagResponse(GameActionResponse):
    game_state: GameState


class RemoveFlagResponse(GameActionResponse):
    game_state: GameState


class HintResponse(GameActionResponse):
    safe_cells: list[Cell]
