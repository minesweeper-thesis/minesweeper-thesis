import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUserWebSocket, OptionalCurrentUser
from backend.routers.schemas import WSRequest
from backend.routers.schemas.game import NewGameRequest, NewGameResponse
from backend.routers.schemas.game.game_schemas import GameActionResponse
from backend.routers.schemas.game.multi_schemas import SessionOverResponse
from backend.routers.schemas.lobby.lobby_schemas import create_game_notification
from backend.routers.websockets.websockets_registry import multi_websockets
from backend.services import exceptions as service_exceptions
from backend.services.lobby_service import SessionOverMessage
from backend.services.singleplayer_service import GenerationTimeout

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


async def notify(receiver_id: uuid.UUID, data):
    if receiver_id in multi_websockets._websockets:
        websocket = multi_websockets.get(receiver_id)
        response = create_game_notification(data)
        await websocket.send_text(response)


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


@game_router.websocket("/single/{gameplay_id}")
async def play_single(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: SingleplayerService,
):
    async def receiver():
        while True:
            data = await websocket.receive_json()
            game_action = WSRequest.from_dict(data)

            action_result = await service.handle_game_action(game_action)
            if action_result is not None:
                await websocket.send_text(
                    GameActionResponse.create(action_result, include_ws_type=True)
                )

            if await service.is_game_over():
                await service.save_gameplay_progress()
                await websocket.close()
                return

    try:
        await websocket.accept()
        game_state = await service.load_gameplay(gameplay_id)
        await websocket.send_text(
            GameActionResponse.create(game_state, include_ws_type=True)
        )

        await receiver()

    except WebSocketDisconnect:
        await service.save_gameplay_progress()
    except GenerationTimeout:
        await websocket.close(code=1001, reason="Board generation timeout")


@game_router.websocket("/multi/{session_id}")
async def play_multi(
    session_id: uuid.UUID,
    websocket: WebSocket,
    service: MultiplayerService,
    user: CurrentUserWebSocket,
):

    async def receiver():
        while True:
            data = await websocket.receive_json()

            if data.get("type") == "ready":
                await service.set_user_ready(session_id, user)
                continue

            if data.get("type") == "not_ready":
                # await service.set_user_not_ready(session_id, user, notify)
                continue

            with suppress(ValueError):
                msg = WSRequest.from_dict(data)
                action_result = await service.handle_game_action(msg)
                await websocket.send_text(
                    GameActionResponse.create(action_result, include_ws_type=True)
                )

                if await service.is_session_over():
                    await websocket.send_text(
                        SessionOverResponse.create(
                            SessionOverMessage(session_id=session_id),
                            include_ws_type=True,
                        )
                    )
                    await websocket.close()
                    return

    service.on_session_end_callback = lambda: websocket.close()

    try:
        await service.set_session(session_id, user, notify)
        await websocket.accept()
        multi_websockets.add(user.id, websocket)

        await receiver()

    except WebSocketDisconnect:
        multi_websockets.remove(user.id)
