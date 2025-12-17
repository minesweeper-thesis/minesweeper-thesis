import uuid
from dataclasses import dataclass

from .common import DifficultyLevel, GenerationSettings

type Minefields = list[tuple[int, int]]


@dataclass
class Board:
    id: uuid.UUID
    minefields: Minefields
    start_field: tuple[int, int]
    generation_settings: GenerationSettings

    @property
    def difficulty_level(self) -> DifficultyLevel:
        return self.generation_settings.difficulty_level


__all__ = ["Board", "Minefields"]
