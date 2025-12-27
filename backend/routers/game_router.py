import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect

from backend import services
from backend.core.game.game_actions import *
from backend.core.multi.session import ReadyChangeLocked
from backend.lib.auth import CurrentUserWebSocket, OptionalCurrentUser
from backend.lib.notification_system import create_game_notification
from backend.lib.websockets.lobby_websockets import lobby_websockets
from backend.schemas.game import NewGameRequest, NewGameResponse
from backend.services import exceptions

CreateSingleGameplayService = Annotated[services.CreateSingleGameplayService, Depends()]
UserConnectionService = Annotated[services.UserConnectionService, Depends()]
PlaySingleService = Annotated[services.PlaySingleService, Depends()]
PlayMultiService = Annotated[services.PlayMultiService, Depends()]
StartRoundService = Annotated[services.StartRoundService, Depends()]
LobbyService = Annotated[services.LobbyService, Depends()]

game_exceptions = {
    exceptions.BoardNotExists: HTTPException(404, "Board not found"),
    exceptions.SolvedAllBoards: HTTPException(
        400, "User solved all boards for this difficulty type"
    ),
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
        case "hint":
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

    except exceptions.GenerationError:
        await websocket.close(code=1001, reason="Board generation error")

    except exceptions.GameplayNotExists:
        await websocket.close(code=1008, reason="Gameplay not found")

    except exceptions.GameplayAlreadyFinished:
        await websocket.close(code=1009, reason="Gameplay already finished")


async def handle_multi(
    user,
    lobby_id: uuid.UUID,
    data,
    play: PlayMultiService,
    start_round: StartRoundService,
):
    match data["type"]:
        case "get_state":
            await play.get_game_state()

        case "ready":
            await start_round.set_user_ready(user, lobby_id)

        case "not_ready":
            await start_round.cancel_user_ready(user, lobby_id)

        case "toggle_ready":
            await start_round.toggle_user_ready(user, lobby_id)

        case _:
            action = _create_action_from_data_multi(data)
            await play.execute_action(action)


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


@game_router.websocket("/multi/{lobby_id}")
async def play_multi(
    lobby_id: uuid.UUID,
    websocket: WebSocket,
    play: PlayMultiService,
    start: StartRoundService,
    user: CurrentUserWebSocket,
    lobby_service: LobbyService,
    user_connection_service: UserConnectionService,
    invitation_id: Optional[uuid.UUID] = None,
):
    try:
        await lobby_service.join_lobby(user, invitation_id) if invitation_id else None
        await play.validate_session(lobby_id, user)
        await websocket.accept()
        lobby_websockets.add(lobby_id, user.id, websocket)
        await user_connection_service.notify_ready_users(user)

        while True:
            data = await websocket.receive_json()
            await play.reload(user)
            await handle_multi(user, lobby_id, data, play, start)

    except exceptions.UserNotInSession:
        await websocket.close(code=1010, reason="User not in multiplayer session")

    except exceptions.SessionNotExists:
        await websocket.close(code=1011, reason="Multiplayer session not found")

    except exceptions.SessionAlreadyOver:
        await websocket.close(code=1012, reason="Multiplayer session is already over")

    except ReadyChangeLocked:
        await websocket.close(
            code=1013, reason="Cannot change ready status at this time"
        )

    except exceptions.InvitationNotExists:
        await websocket.close(code=1014, reason="Invitation not found")

    except WebSocketDisconnect:
        pass

    finally:
        lobby_websockets.remove(lobby_id, user.id)
