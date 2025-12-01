import uuid
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator

from backend.core.board import (
    DifficultyLevel,
    GenerationSettings,
    GeneratorParams,
    GeneratorType,
)
from backend.core.game import *
from backend.services.single.singleplayer_service import NewGameSettings


class GenerationRequest(BaseModel):
    type: GeneratorType
    settings: Optional[GeneratorParams] = Field(
        None, description="Required if generator_type is set to 'ml'"
    )


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
                GenerationSettings(
                    self.generator.type,
                    self.difficulty_level,
                    self.generator.settings,
                )
                if self.generator and self.difficulty_level
                else None
            ),
            difficulty_level=self.difficulty_level,
            mode=self.mode,
        )


class NewGameResponse(BaseModel):
    gameplay_id: uuid.UUID


__all__ = ["NewGameRequest", "NewGameResponse"]
