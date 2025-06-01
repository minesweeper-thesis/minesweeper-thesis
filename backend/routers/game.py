from fastapi import APIRouter

from algorithms.boards.random_board import RandomBoard

from ..db import *
from ..models import *

game_router = APIRouter()


@game_router.get("/board")
async def get_board(rows: int, cols: int, start_x: int, start_y: int, mine_count: int):
    print(rows, cols, (start_x, start_y), mine_count)
    board = RandomBoard(rows, cols, (start_x, start_y), mine_count)
    board.grid().print_solved()
    return board.grid().grid
