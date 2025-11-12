import asyncio
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUser, CurrentUserWebSocket
from backend.routers.schemas import create_response

from .schemas.lobby_schemas import *

LobbyService = Annotated[services.LobbyService, Depends()]

lobby_router = APIRouter(tags=["lobby"])

user_websockets: dict[uuid.UUID, WebSocket] = {}
online_users: set[uuid.UUID] = set()


async def notify(receiver_id: uuid.UUID, data: Any):
    await user_websockets[receiver_id].send_text(create_response(data))


def is_user_online(user_id: uuid.UUID) -> bool:
    return user_id in online_users


@lobby_router.post("")
async def create_lobby(
    user: CurrentUser,
    service: LobbyService,
) -> InvitationLobbyResponse:
    """Creates a new lobby."""
    lobby = await service.create_lobby(user)
    return InvitationLobbyResponse.create(lobby)


@lobby_router.post("/{lobby_id}")
async def update_lobby_config(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    config: UpdateGameConfigRequest,
):
    await service.update_lobby(lobby_id, user, config.game_config, notify)


@lobby_router.post("/{lobby_id}/invite/{user_id}")
async def invite_user_to_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    user_id: uuid.UUID,
):
    await service.invite_to_lobby(lobby_id, user, user_id, notify)


@lobby_router.post("/join/{invitation_id}")
async def join_lobby(
    service: LobbyService,
    user: CurrentUser,
    invitation_id: uuid.UUID,
):
    lobby = await service.join_lobby(user, invitation_id, notify)
    return LobbyResponse.create(lobby)


@lobby_router.post("/leave/{lobby_id}")
async def leave_lobby(
    service: LobbyService,
    user: CurrentUser,
    lobby_id: uuid.UUID,
):
    """Leaves the lobby."""
    await service.remove_user_from_lobby(lobby_id, user, notify)


@lobby_router.delete("/invitation/{invitation_id}")
async def reject_game_invitation(
    user: CurrentUser,
    service: LobbyService,
    invitation_id: uuid.UUID,
):
    """Rejects a game invitation."""
    await service.reject_game_invitation(invitation_id, user, notify)


@lobby_router.websocket("/ws")
async def send_notifications(
    websocket: WebSocket,
    user: CurrentUserWebSocket,
):
    """WebSocket endpoint for receiving game invitations."""
    online_users.add(user.id)

    try:
        await websocket.accept()
        user_websockets[user.id] = websocket
        while True:
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        online_users.discard(user.id)
        user_websockets.pop(user.id, None)
