import random
import uuid
from dataclasses import asdict, dataclass
from typing import Literal, Optional

from algorithms.generator import Generator as GeneratorAlgorithm
from algorithms.generator import RandomGenerator

type ClassifierType = Literal["lightgbm", "catboost", "gaussiannb", "xgboost"]
type HeuristicType = Literal["no", "naive", "GA", "MCTS", "PSO", "SA"]
type GeneratorType = Literal["random", "ml"]

type Minefields = list[tuple[int, int]]


@dataclass
class DifficultyLevel:
    rows: int
    columns: int
    mine_count: int


@dataclass
class GeneratorParams:
    classifier: ClassifierType
    heuristic: HeuristicType
    heuristic_args: tuple[float | int, ...] = tuple()


@dataclass
class GenerationSettings:
    type: GeneratorType
    difficulty_level: DifficultyLevel
    settings: Optional[GeneratorParams] = None


@dataclass
class Board:
    id: uuid.UUID
    difficulty_level: DifficultyLevel
    _minefields: Optional[Minefields]
    _start_field: Optional[tuple[int, int]]
    generation_settings: GenerationSettings

    @property
    def is_generated(self) -> bool:
        return self._minefields is not None and self._start_field is not None

    def get_start_field(self) -> tuple[int, int]:
        if self._start_field is None:
            raise RuntimeError("Board is not generated yet")

        return self._start_field

    def get_minefields(self) -> Minefields:
        if self._minefields is None:
            raise RuntimeError("Board is not generated yet")

        return self._minefields


class BoardGenerator:
    def __init__(
        self,
        difficulty_level: DifficultyLevel,
        type: GeneratorType,
        settings: Optional[GeneratorParams] = None,
    ) -> None:
        self.difficulty_level = difficulty_level
        self.type: GeneratorType = type
        self.settings = settings

    def generate_board(self) -> Board:
        rows = self.difficulty_level.rows
        columns = self.difficulty_level.columns
        start_field = (
            random.randint(0, rows - 1),
            random.randint(0, columns - 1),
        )

        generator = self._get_generator(start_field)
        minefields = generator.generate().grid().mined_fields

        return Board(
            id=uuid.uuid4(),
            difficulty_level=self.difficulty_level,
            _minefields=minefields,
            _start_field=start_field,
            generation_settings=GenerationSettings(
                type=self.type,
                difficulty_level=self.difficulty_level,
                settings=self.settings,
            ),
        )

    def _get_generator(self, start_field):
        generator_settings = self.settings

        if self.type == "random":
            return RandomGenerator(
                **asdict(self.difficulty_level), start_field=start_field
            )

        elif self.type == "ml":
            if generator_settings is None:
                raise ValueError(
                    "Generator settings must be provided for deterministic generation"
                )

            return GeneratorAlgorithm(
                **asdict(generator_settings),
                **asdict(self.difficulty_level),
                start_field=start_field,
                classifier_iterations=6400,
            )
        else:
            raise ValueError(f"Unknown generator type: {self.type}")


__all__ = [
    "Board",
    "Minefields",
    "BoardGenerator",
    "DifficultyLevel",
    "GenerationSettings",
    "GeneratorParams",
    "ClassifierType",
    "HeuristicType",
    "GeneratorType",
]
