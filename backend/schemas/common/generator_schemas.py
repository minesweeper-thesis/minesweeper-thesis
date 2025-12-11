from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator

from backend.core.board import (
    ClassifierType,
    GeneratorParams,
    GeneratorType,
    HeuristicType,
)
from backend.core.game import *
from backend.core.multi import Generator


class GeneratorParamsSchema(BaseModel):
    classifier: ClassifierType
    heuristic: HeuristicType = "no"
    heuristic_args: tuple[int | float, ...] = tuple()

    @model_validator(mode="after")
    def validate_heuristic_args(self) -> Self:
        args = self.heuristic_args

        if self.heuristic == "no":
            if len(args) != 0:
                raise ValueError("no heuristic_args must be empty!")

        elif self.heuristic == "naive":
            if len(args) != 1:
                raise ValueError("naive heuristic_args must have 1 item!")

            (tries,) = args

            if not (1 <= tries <= 1000) or not isinstance(tries, int):
                raise ValueError("naive heuristic_args must be an int in [1, 1000].")

        elif self.heuristic == "GA":
            if len(args) != 4:
                raise ValueError("GA heuristic_args must have 4 items!")

            generations, population_size, parents_size, random_specimen_rate = args

            if not (1 <= generations <= 100) or not isinstance(generations, int):
                raise ValueError("GA generations must be an int in [1, 100].")
            if not (1 <= population_size <= 100) or not isinstance(
                population_size, int
            ):
                raise ValueError("GA population_size must be an int in [1, 100].")
            if not (1 <= parents_size <= 100) or not isinstance(parents_size, int):
                raise ValueError("GA parents_size must be an int in [1, 100].")
            if not (0.0 <= random_specimen_rate <= 1.0):
                raise ValueError("GA random_specimen_rate must be in [0.0, 1.0].")

        elif self.heuristic == "PSO":
            if len(args) != 5:
                raise ValueError("PSO heuristic_args must have 5 items!")

            iterations, particle_count, rate1, rate2, rate3 = args

            if not (1 <= iterations <= 100) or not isinstance(iterations, int):
                raise ValueError("PSO iterations must be an int in [1, 100].")
            if not (1 <= particle_count <= 100) or not isinstance(particle_count, int):
                raise ValueError("PSO particle_count must be an int in [1, 100].")
            if not (0.4 <= rate1 <= 0.9):
                raise ValueError("PSO rate1 must be in [0.4, 0.9].")
            if not (1.0 <= rate2 <= 2.5):
                raise ValueError("PSO rate2 must be in [1.0, 2.5].")
            if not (1.0 <= rate3 <= 2.5):
                raise ValueError("PSO rate3 must be in [1.0, 2.5].")

        elif self.heuristic == "SA":
            if len(args) != 4:
                raise ValueError("SA heuristic_args must have 4 items!")

            iterations, fields_changed, t_min, t_max = args

            if not (1 <= iterations <= 100) or not isinstance(iterations, int):
                raise ValueError("SA iterations must be an int in [1, 100].")
            if not (1 <= fields_changed <= 50) or not isinstance(fields_changed, int):
                raise ValueError("SA fields_changed must be an int in [1, 50].")
            if not (1.0 <= t_min <= 100.0):
                raise ValueError("SA t_max must be in [1.0, 100.0].")
            if not (0.1 <= t_max <= 1.0):
                raise ValueError("SA t_min must be in [0.1, 1.0].")

        else:
            raise ValueError(f"Unknown heuristic type: {self.heuristic}")

        return self


class GeneratorSchema(BaseModel):
    type: GeneratorType
    settings: Optional[GeneratorParamsSchema] = Field(
        None, description="Required if generator.type is set to 'ml'"
    )

    def to_generator(self) -> Generator:
        return Generator(
            self.type,
            GeneratorParams(**self.settings.model_dump()) if self.settings else None,
        )

    @classmethod
    def from_generator(cls, generator: Generator) -> Self:
        return cls.model_construct(
            type=generator.generator_type, settings=generator.settings
        )


__all__ = ["GeneratorSchema"]
