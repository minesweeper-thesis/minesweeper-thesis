from typing import Annotated

from fastapi import Depends

from algorithms.generator import Generator, RandomGenerator
from backend import repositories
from backend.models.board_models import Board
from backend.schemas.board_schemas import GenerationInput

BoardRepository = Annotated[repositories.BoardRepository, Depends()]


class BoardService:
    def __init__(self, repo: BoardRepository):
        self.repo = repo

    async def generate_board(self, generation_input: GenerationInput) -> Board:
        generator = self._get_generator(generation_input)
        minefields = generator.generate().grid().grid

        board = await self._create_board(generation_input.difficulty_level, minefields)
        return board

    def _get_generator(self, generation_input: GenerationInput):
        generator_settings = generation_input.generator_settings
        difficulty_level = generation_input.difficulty_level
        start_field = generation_input.start_field

        if generation_input.generator_type == "random":
            return RandomGenerator(
                **difficulty_level.model_dump(), start_field=start_field
            )

        elif generation_input.generator_type == "deterministic":
            if generator_settings is None:
                raise ValueError(
                    "Generator settings must be provided for deterministic generation"
                )

            return Generator(
                **generator_settings.model_dump(),
                **difficulty_level.model_dump(),
                start_field=start_field,
                classifier_iterations=6400,
            )
        else:
            raise ValueError(
                f"Unknown generator type: {generation_input.generator_type}"
            )

    async def _create_board(self, difficulty_level, minefields):
        board_type = await self.repo.get_board_type(**difficulty_level.model_dump())
        board = Board(board_type_id=board_type.id, minefields=minefields)

        return await self.repo.add_board(board)
