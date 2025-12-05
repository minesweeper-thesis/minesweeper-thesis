import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.core.game.game_actions import *
from backend.lib.auth import CurrentUserWebSocket, OptionalCurrentUser
from backend.lib.notification_system import create_game_notification
from backend.lib.websockets.websockets_registry import multi_websockets
from backend.routers.schemas.game import NewGameRequest, NewGameResponse
from backend.services import exceptions
from backend.services.single.single_exceptions import GenerationTimeout

CreateSingleGameplayService = Annotated[services.CreateSingleGameplayService, Depends()]
PlaySingleService = Annotated[services.PlaySingleService, Depends()]
PlayMultiService = Annotated[services.PlayMultiService, Depends()]
StartRoundService = Annotated[services.StartRoundService, Depends()]
LobbyService = Annotated[services.LobbyService, Depends()]

game_exceptions = {
    exceptions.BoardNotExists: HTTPException(404, "Board not found"),
    exceptions.SolvedAllBoards: HTTPException(
        400, "User solved all boards for this difficulty type"
    ),
    exceptions.GameplayAlreadyFinished: HTTPException(
        400, "Gameplay is already finished"
    ),
    exceptions.GameplayNotExists: HTTPException(404, "Gameplay not found"),
}


game_router = APIRouter(tags=["game"])


@game_router.post("/single")
async def start_singleplayer_game(
    new_game_input: NewGameRequest,
    user: OptionalCurrentUser,
    service: CreateSingleGameplayService,
) -> NewGameResponse:
    gameplay_id = await service.create_singleplayer_gameplay(
        user, new_game_input.to_game_settings()
    )
    return NewGameResponse(gameplay_id=gameplay_id)


async def handle(data, service: PlaySingleService):
    if data["type"] == "get_state":
        return service.get_game_state()

    action = _create_action_from_data(data)
    return await service.execute_action(action)


def _create_action_from_data(data) -> GameAction:
    match data["type"]:
        case "reveal_one":
            return RevealOneAction(cell=(data["cell"][0], data["cell"][1]))
        case "reveal_many":
            return RevealManyAction(cell=(data["cell"][0], data["cell"][1]))
        case "flag":
            return FlagAction(cell=(data["cell"][0], data["cell"][1]))
        case "remove_flag":
            return RemoveFlagAction(cell=(data["cell"][0], data["cell"][1]))
        case "use_hint":
            return UseHintAction()
        case _:
            raise ValueError(f"Unknown action type: {data['type']}")


@game_router.websocket("/single/{gameplay_id}")
async def play_single(
    gameplay_id: uuid.UUID,
    websocket: WebSocket,
    service: PlaySingleService,
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
                result = await service.get_game_over_result()
                await websocket.send_text(create_game_notification(result))
                break

        await websocket.close()

    except WebSocketDisconnect:
        await service.save_gameplay_progress()

    except GenerationTimeout:
        await websocket.close(code=1001, reason="Board generation timeout")


async def handle_multi(
    user,
    session_id,
    data,
    play: PlayMultiService,
    start_round: StartRoundService,
):
    match data["type"]:
        case "get_state":
            play.get_game_state()
            return [(user.id, play.get_game_state())]

        case "ready":
            await start_round.set_user_ready(session_id, user)

        case "not_ready":
            await start_round.cancel_user_ready(session_id, user)

        case "toggle_ready":
            await start_round.toggle_user_ready(session_id, user)

        case _:
            action = _create_action_from_data_multi(data)
            await play.execute_action(action)

    return play.collect_messages()


def _create_action_from_data_multi(data) -> GameAction:
    match data["type"]:
        case "reveal_one":
            return RevealOneAction(cell=(data["cell"][0], data["cell"][1]))
        case "reveal_many":
            return RevealManyAction(cell=(data["cell"][0], data["cell"][1]))
        case "flag":
            return FlagAction(cell=(data["cell"][0], data["cell"][1]))
        case "remove_flag":
            return RemoveFlagAction(cell=(data["cell"][0], data["cell"][1]))
        case _:
            raise ValueError(f"Unknown action type: {data['type']}")


async def send(user_id: uuid.UUID, message: Any):
    if user_id in multi_websockets._websockets:
        websocket = multi_websockets.get(user_id)
        response = create_game_notification(message)
        await websocket.send_text(response)


@game_router.websocket("/multi/{session_id}")
async def play_multi(
    session_id: uuid.UUID,
    websocket: WebSocket,
    play: PlayMultiService,
    start: StartRoundService,
    user: CurrentUserWebSocket,
):
    try:
        await websocket.accept()
        multi_websockets.add(user.id, websocket)

        await play.set_session(session_id, user)

        while True:
            data = await websocket.receive_json()
            messages = await handle_multi(user, session_id, data, play, start)

            for user_id, message in messages:
                await send(user_id, message)

            if play.is_session_over():
                break

        await websocket.close()

    except WebSocketDisconnect:
        multi_websockets.remove(user.id)
