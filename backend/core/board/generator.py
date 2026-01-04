import random
import uuid
from dataclasses import asdict
from typing import Optional

from algorithms.generator import Generator, RandomGenerator
from backend.lib.generator.classifier_provider import get_classifier

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

            classifier = get_classifier(
                self.difficulty_level, generator_settings.classifier
            )
            assert classifier is not None, "Classifier is None"

            return Generator(
                classifier,
                heuristic=generator_settings.heuristic,
                heuristic_args=generator_settings.heuristic_args,
                **asdict(self.difficulty_level),
                start_field=start_field,
            )
        else:
            raise ValueError(f"Unknown generator type: {self.type}")


__all__ = ["BoardGenerator"]
