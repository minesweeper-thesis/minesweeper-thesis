import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.core.game import GameAction, GameActionResult
from backend.core.multi.session import MultiplayerResult
from backend.lib.auth import CurrentUserWebSocket, OptionalCurrentUser
from backend.routers.schemas import WSRequest
from backend.routers.schemas.game import NewGameRequest, NewGameResponse
from backend.routers.schemas.lobby.lobby_schemas import create_game_notification
from backend.routers.websockets.websockets_registry import multi_websockets
from backend.services import exceptions as service_exceptions
from backend.services.multiplayer_service import MultiplayerGameTransport
from backend.services.singleplayer_service import (
    GenerationTimeout,
    SingleplayerGameTransport,
)

SingleplayerService = Annotated[services.SingleplayerService, Depends()]
MultiplayerService = Annotated[services.MultiplayerService, Depends()]
LobbyService = Annotated[services.LobbyService, Depends()]

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


game_router = APIRouter(tags=["game"])


@game_router.post("/single")
async def start_singleplayer_game(
    new_game_input: NewGameRequest,
    user: OptionalCurrentUser,
    service: SingleplayerService,
) -> NewGameResponse:
    gameplay_id = await service.create_singleplayer_gameplay(
        user, new_game_input.to_game_settings()
    )
    return NewGameResponse(gameplay_id=gameplay_id)


class SingleplayerWebSocketTransport(SingleplayerGameTransport):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def receive_action(self) -> GameAction:
        data = await self.websocket.receive_json()
        return WSRequest.from_dict(data)

    async def send(self, result: GameActionResult):
        await self.websocket.send_text(create_game_notification(result))

    async def close(self):
        await self.websocket.close()


@game_router.websocket("/single/{gameplay_id}")
async def play_single(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: SingleplayerService,
):
    try:
        await websocket.accept()
        await service.load_gameplay(
            gameplay_id, SingleplayerWebSocketTransport(websocket)
        )

        await service.game_loop()

    except WebSocketDisconnect:
        await service.save_gameplay_progress()

    except GenerationTimeout:
        await websocket.close(code=1001, reason="Board generation timeout")


class MultiplayerWebSocketTransport(MultiplayerGameTransport):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def receive(self) -> GameAction:
        data = await self.websocket.receive_json()
        return WSRequest.from_dict(data)

    async def send(self, user_id: uuid.UUID, result: MultiplayerResult):
        if user_id in multi_websockets._websockets:
            websocket = multi_websockets.get(user_id)
            response = create_game_notification(result)
            await websocket.send_text(response)

    async def close(self):
        await self.websocket.close()


@game_router.websocket("/multi/{session_id}")
async def play_multi(
    session_id: uuid.UUID,
    websocket: WebSocket,
    service: MultiplayerService,
    user: CurrentUserWebSocket,
):
    try:
        transport = MultiplayerWebSocketTransport(websocket)
        await service.set_session(session_id, user, transport)

        await websocket.accept()
        multi_websockets.add(user.id, websocket)

        await service.session_loop()

    except WebSocketDisconnect:
        multi_websockets.remove(user.id)
