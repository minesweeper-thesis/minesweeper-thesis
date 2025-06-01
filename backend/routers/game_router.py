import uuid

from fastapi import APIRouter, Depends, Response

from backend.services import auth_service, game_service, user_service

from ..db import *
from ..models import *
from ..schemas import *

game_router = APIRouter()


@game_router.get("/board")
async def get_board(rows: int, cols: int, start_x: int, start_y: int, mine_count: int):
    return game_service.generate_random_board(rows, cols, start_x, start_y, mine_count)
