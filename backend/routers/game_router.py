import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUser, CurrentUserWebSocket, OptionalCurrentUser
from backend.routers.schemas import create_response
from backend.services import exceptions as service_exceptions

from .schemas.game_schemas import *

SingleplayerService = Annotated[services.SingleplayerService, Depends()]
MultiplayerService = Annotated[services.MultiplayerService, Depends()]

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
    gameplay, board = await service.create_singleplayer_gameplay(
        user, new_game_input.to_game_settings()
    )
    return NewGameResponse(
        gameplay_id=gameplay.id,
        board_id=board.id,
        start_field=board.start_field,
    )


@game_router.websocket("/single/{gameplay_id}")
async def play_single(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: SingleplayerService,
):
    async def receiver():
        while True:
            data = await websocket.receive_json()
            game_action = parse_game_action(data)

            action_result, is_game_over = await service.handle_game_action(game_action)
            if action_result is not None:
                await websocket.send_text(create_response(action_result))

            if is_game_over:
                await service.save_gameplay_progress()
                await websocket.close()
                return

    try:
        await service.load_gameplay(gameplay_id)
        await websocket.accept()

        await receiver()

    except WebSocketDisconnect:
        await service.save_gameplay_progress()


@game_router.post("/{lobby_id}/ready")
async def set_user_ready(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    # service: LobbyService,
):
    """Sets the user as ready in the lobby."""
    # await service.set_user_ready(lobby_id, user, notify)


@game_router.websocket("/multi/{session_id}")
async def play_multi(
    session_id: uuid.UUID,
    websocket: WebSocket,
    service: MultiplayerService,
    user: CurrentUserWebSocket,
):
    async def send_round_start(start_time, end_time):
        await websocket.send_text(
            RoundStartResponse(
                start_at=start_time,
                end_at=end_time,
            ).model_dump_json(exclude_none=True)
        )

    async def send_round_end():
        await websocket.send_text(RoundEndResponse().model_dump_json(exclude_none=True))

    async def send_data(data):
        await websocket.send_text(create_response(data))  # todo: create_response

    async def receiver():
        while True:
            data = await websocket.receive_json()

            with suppress(ValueError):
                msg = parse_multiplayer_session_message(data)
                await service.handle_multiplayer_session_message(msg)

            with suppress(ValueError):
                msg = parse_game_action(data)
                action_result, is_session_over = await service.handle_game_action(msg)
                await websocket.send_text(create_response(action_result))

                if is_session_over:
                    await websocket.send_text(
                        SessionEndResponse().model_dump_json(
                            exclude_none=True
                        )  # todo: add ranking
                    )
                    await websocket.close()
                    return

    try:
        await service.load_session(session_id, user, send_data)
        await websocket.accept()

        await receiver()

    except WebSocketDisconnect:
        pass
