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
class GeneratorSettings:
    classifier: ClassifierType
    heuristic: HeuristicType
    heuristic_args: tuple[float | int, ...] = tuple()


@dataclass
class Board:
    id: uuid.UUID
    difficulty_level: DifficultyLevel
    minefields: Minefields
    start_field: tuple[int, int]


@dataclass
class GenerationSettings:
    type: GeneratorType
    settings: Optional[GeneratorSettings] = None


class BoardGenerator:
    def __init__(
        self,
        difficulty_level: DifficultyLevel,
        type: GeneratorType,
        settings: Optional[GeneratorSettings] = None,
    ) -> None:
        self.difficulty_level = difficulty_level
        self.type = type
        self.settings = settings

    async def generate_board(self) -> Board:
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
            minefields=minefields,
            start_field=start_field,
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
