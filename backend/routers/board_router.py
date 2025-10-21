from typing import Annotated

from fastapi import APIRouter, Depends

from backend import services
from backend.schemas.board import *

board_router = APIRouter(tags=["gameplay"])

BoardService = Annotated[services.BoardService, Depends()]

DIFFICULTY_LEVELS = [(10, 10, 15), (16, 16, 40), (16, 30, 99)]


@board_router.post("/generate_board")
async def generate_board(
    generator_input: GenerationInput, service: BoardService
) -> GenerationOutput:
    """Returns generated board ID."""
    board_id = await service.generate_board(generator_input)
    return GenerationOutput(board_id=board_id)
