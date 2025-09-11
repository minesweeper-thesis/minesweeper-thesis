from fastapi import APIRouter

from backend.services import game_service

from ..db import *
from ..models import *
from ..schemas import *

game_router = APIRouter()

DIFFICULTY_LEVELS = [(10, 10, 15), (16, 16, 40), (16, 30, 99)]


@game_router.post("/board", response_model=BoardSchema)
async def get_board(generator_input: GeneratorInput):
    """Generates a board as `list[list[int]]`"""

    difficulty_level = (
        generator_input.rows,
        generator_input.columns,
        generator_input.mine_count,
    )

    if difficulty_level not in DIFFICULTY_LEVELS:
        return game_service.generate_random_board(generator_input)

    return game_service.generate_board(generator_input)
