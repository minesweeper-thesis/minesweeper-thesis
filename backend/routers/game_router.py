import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUserWebSocket, OptionalCurrentUser
from backend.lib.notification_system import create_game_notification
from backend.routers.schemas import WSRequest
from backend.routers.schemas.game import NewGameRequest, NewGameResponse
from backend.routers.websockets.websockets_registry import multi_websockets
from backend.services import exceptions as service_exceptions
from backend.services.multiplayer_service import (
    MultiplayerGameTransport,
    MultiplayerResult,
)
from backend.services.single.game_actions import *
from backend.services.single.singleplayer_service import GenerationTimeout

CreateSingleplayerGameplayUseCase = Annotated[
    services.CreateSingleplayerGameplayUseCase, Depends()
]
SingleplayerGameplayUseCase = Annotated[services.SingleplayerGameplayUseCase, Depends()]
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
    service: CreateSingleplayerGameplayUseCase,
) -> NewGameResponse:
    gameplay_id = await service.create_singleplayer_gameplay(
        user, new_game_input.to_game_settings()
    )
    return NewGameResponse(gameplay_id=gameplay_id)


async def handle(data, service: SingleplayerGameplayUseCase):
    if data["type"] == "get_game_state":
        return service.get_game_state()

    action = _create_action_from_data(data)
    return await service.execute_action(action)


def _create_action_from_data(data) -> GameAction:
    match data["type"]:
        case "reveal_one":
            return RevealOneAction(cell=(data["x"], data["y"]))
        case "reveal_many":
            return RevealManyAction(cell=(data["x"], data["y"]))
        case "flag":
            return FlagAction(cell=(data["x"], data["y"]))
        case "remove_flag":
            return RemoveFlagAction(cell=(data["x"], data["y"]))
        case "use_hint":
            return UseHintAction()
        case _:
            raise ValueError(f"Unknown action type: {data['type']}")


@game_router.websocket("/single/{gameplay_id}")
async def play_single(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: SingleplayerGameplayUseCase,
):
    try:
        await websocket.accept()
        game_state = await service.load_gameplay(gameplay_id)
        await websocket.send_text(create_game_notification(game_state))

        while True:
            data = await websocket.receive_json()
            result = await handle(data, service)

            if result is not None:
                await websocket.send_text(create_game_notification(result))

            if await service.is_game_over():
                await service.save_gameplay_progress()
                break

        await websocket.close()

    except WebSocketDisconnect:
        await service.save_gameplay_progress()

    except GenerationTimeout:
        await websocket.close(code=1001, reason="Board generation timeout")


class MultiplayerWebSocketTransport(MultiplayerGameTransport):
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket

    async def receive(self):
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
        await websocket.accept()
        multi_websockets.add(user.id, websocket)
        transport = MultiplayerWebSocketTransport(websocket)

        await service.set_session(session_id, user, transport)

        await service.session_loop()

    except WebSocketDisconnect:
        multi_websockets.remove(user.id)
