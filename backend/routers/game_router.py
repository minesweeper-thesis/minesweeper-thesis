import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.schemas.game_schemas import *
from backend.services import exceptions as service_exceptions
from backend.services.auth_service import OptionalCurrentUser

GameService = Annotated[services.GameService, Depends()]

game_exceptions = {
    service_exceptions.BoardNotExists: HTTPException(404, "Board not found"),
    service_exceptions.SolvedAllBoards: HTTPException(
        400, "User solved all boards for this difficulty type"
    ),
    service_exceptions.GameplayAlreadyFinished: HTTPException(
        400, "Gameplay is already finished"
    ),
    service_exceptions.GameplayNotExists: HTTPException(404, "Gameplay not found"),
}


game_router = APIRouter(prefix="/game", tags=["game"])


@game_router.post("/single/init")
async def start_singleplayer_game(
    new_game_input: NewGameInput, user: OptionalCurrentUser, service: GameService
) -> NewGameResponse:
    """Starts a new game."""
    return await service.create_singleplayer_gameplay(user, new_game_input)


@game_router.websocket("/{gameplay_id}/ws")
async def play_game_via_websocket(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: GameService,
):
    """WebSocket endpoint for playing a game."""

    async def sender():
        return
        while True:
            await asyncio.sleep(2)
            await websocket.send_text("Serwer: ping")

    async def receiver():
        while True:
            data = await websocket.receive_json()
            game_action = parse_game_action(data)

            action_result, is_game_over = await service.handle_game_action(game_action)
            await websocket.send_json(action_result.model_dump(exclude_none=True))

            if is_game_over:
                await service.save_gameplay_progress()
                await websocket.close()
                return

    try:
        await service.load_gameplay(gameplay_id)
        await websocket.accept()

        await asyncio.gather(sender(), receiver())

    except WebSocketDisconnect:
        await service.save_gameplay_progress()
