import random
import uuid
from dataclasses import asdict
from typing import Optional

from algorithms.generator import Generator, RandomGenerator

from .board import Board
from .common import *


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
            minefields=minefields,
            start_field=start_field,
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

            return Generator(
                **asdict(generator_settings),
                **asdict(self.difficulty_level),
                start_field=start_field,
                version=get_classifier_version(
                    generator_settings.classifier, self.difficulty_level
                ),
            )
        else:
            raise ValueError(f"Unknown generator type: {self.type}")


def get_classifier_version(
    classifier: ClassifierType, difficulty_level: DifficultyLevel
) -> str:
    rows = difficulty_level.rows
    columns = difficulty_level.columns
    mine_count = difficulty_level.mine_count
    mapping = {
        (10, 10, 15, "lightgbm"): "12800",
        (16, 16, 40, "lightgbm"): "12800",
        (16, 30, 99, "lightgbm"): "400",
        (10, 10, 15, "catboost"): "6400",
        (16, 16, 40, "catboost"): "3200",
        (16, 30, 99, "catboost"): "1600",
        (10, 10, 15, "xgboost"): "6400",
        (16, 16, 40, "xgboost"): "6400",
        (16, 30, 99, "xgboost"): "3200",
        (10, 10, 15, "gaussiannb"): "",
        (16, 16, 40, "gaussiannb"): "",
        (16, 30, 99, "gaussiannb"): "",
    }

    key = (rows, columns, mine_count, classifier)

    if key not in mapping:
        raise ValueError(
            f"No classifier version found for {classifier} with difficulty {rows}x{columns} and {mine_count} mines"
        )

    return mapping[key]


__all__ = ["BoardGenerator"]
