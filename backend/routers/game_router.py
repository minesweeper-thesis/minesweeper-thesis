import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket

from backend import services
from backend.schemas.game_schemas import *
from backend.services.auth_service import OptionalCurrentUser

game_router = APIRouter(prefix="/game", tags=["game"])

GameService = Annotated[services.GameService, Depends()]


@game_router.post("/single/start")
async def start_singleplayer_game(
    new_game_input: NewGameInput, user: OptionalCurrentUser, service: GameService
) -> NewGameResponse:
    """Starts a new game."""
    return await service.create_singleplayer_session(user, new_game_input)


@game_router.websocket("/{gameplay_id}/ws")
async def play_game_via_websocket(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: GameService,
):
    await websocket.accept()

    async def sender():
        return
        while True:
            await asyncio.sleep(2)
            await websocket.send_text("Serwer: ping")

    async def receiver():
        while True:
            data = await websocket.receive_json()
            game_action = parse_game_action(data)
            res = await service.handle_game_action(gameplay_id, game_action)
            await websocket.send_json(res)
            if res.get("full_board") is not None:
                await websocket.close()
                return

    await asyncio.gather(sender(), receiver())
