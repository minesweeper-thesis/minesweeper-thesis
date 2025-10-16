from typing import Annotated

from fastapi import APIRouter, Depends

from backend import schemas, services

game_router = APIRouter(tags=["gameplay"])

GameService = Annotated[services.GameService, Depends()]

DIFFICULTY_LEVELS = [(10, 10, 15), (16, 16, 40), (16, 30, 99)]


@game_router.post("/board", response_model=schemas.Board)
async def get_board(generator_input: schemas.GeneratorInput, service: GameService):
    """Generates a board as `list[list[int]]`"""

    difficulty_level = (
        generator_input.rows,
        generator_input.columns,
        generator_input.mine_count,
    )

    if difficulty_level not in DIFFICULTY_LEVELS:
        return service.generate_random_board(generator_input)

    return service.generate_board(generator_input)
