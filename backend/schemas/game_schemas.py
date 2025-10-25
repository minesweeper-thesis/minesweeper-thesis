import uuid
from typing import Literal, Optional, Self

from pydantic import BaseModel, Field, model_validator

from backend.schemas.board_schemas import *


class NewGameInput(BaseModel):
    board_id: Optional[uuid.UUID] = Field(
        None,
        description="Use existing board (exclusive with generation_settings, difficulty_level)",
    )
    generation_settings: Optional[GenerationInput] = Field(
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
        generation_settings = self.generation_settings
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
    type: str


class RevealOne(GameAction):
    type: str = "reveal_one"
    x: int
    y: int


class RevealMany(GameAction):
    type: str = "reveal_many"
    x: int
    y: int


class Flag(GameAction):
    type: str = "flag"
    x: int
    y: int


class RemoveFlag(GameAction):
    type: str = "remove_flag"
    x: int
    y: int


def parse_game_action(data: dict) -> GameAction:
    try:
        action_type = data["type"]

        model_map = {
            "reveal_one": RevealOne,
            "reveal_many": RevealMany,
            "flag": Flag,
            "remove_flag": RemoveFlag,
        }

        return model_map[action_type](**data)
    except:
        raise ValueError(f"Unknown action type: {action_type}")


type GameState = Literal["in_progress", "won", "lost"]


class RevealedCell(BaseModel):
    x: int
    y: int
    value: int


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
