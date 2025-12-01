import uuid
from dataclasses import dataclass
from typing import Optional

from backend.core.board import DifficultyLevel, GeneratorParams, GeneratorType
from backend.core.game import GameMode


@dataclass
class GameConfig:
    rounds: int
    max_round_time: int
    difficulty_level: DifficultyLevel
    game_mode: GameMode
    generator_type: GeneratorType
    generator_settings: Optional[GeneratorParams] = None


@dataclass
class GameConfigUpdated:
    lobby_id: uuid.UUID
    game_config: GameConfig
