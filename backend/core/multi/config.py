import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.board import (
    DifficultyLevel,
    GenerationSettings,
    GeneratorParams,
    GeneratorType,
)
from backend.core.game import GameMode


@dataclass
class GameConfig:
    rounds: int
    max_round_time: int
    difficulty_level: DifficultyLevel
    game_mode: GameMode
    generator_type: GeneratorType
    generator_settings: Optional[GeneratorParams] = None

    @property
    def generation_settings(self) -> GenerationSettings:
        return GenerationSettings(
            type=self.generator_type,
            difficulty_level=self.difficulty_level,
            settings=self.generator_settings,
        )


@dataclass
class GameConfigUpdated:
    lobby_id: uuid.UUID
    game_config: GameConfig


__all__ = ["GameConfig", "GameConfigUpdated"]
