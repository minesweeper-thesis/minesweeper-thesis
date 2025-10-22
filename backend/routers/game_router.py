from typing import Annotated

from fastapi import APIRouter, Depends

from backend import services
from backend.schemas.game_schemas import *
from backend.services.auth_service import OptionalCurrentUser

game_router = APIRouter(prefix="/game", tags=["game"])

GameService = Annotated[services.GameService, Depends()]


@game_router.post("/start")
async def start_singleplayer_game(
    new_game_input: NewGameInput, user: OptionalCurrentUser, service: GameService
) -> NewGameOutput:
    """Starts a new game."""
    return await service.start_singleplayer_game(user, new_game_input)
