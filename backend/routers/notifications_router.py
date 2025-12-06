from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUserWebSocket
from backend.lib.websockets.connections_manager import connections_manager
from backend.routers.schemas import WSRequest
from backend.routers.schemas.lobby import (
    CurrentLobbyResponse,
    PendingInvitationsResponse,
)

LobbyService = Annotated[services.LobbyService, Depends()]

notifications_router = APIRouter(tags=["notifications"])


@notifications_router.websocket("/ws")
async def send_notifications(
    websocket: WebSocket,
    user: CurrentUserWebSocket,
    lobby_service: LobbyService,
):
    connections_manager.add(user.id, websocket)

    async def receiver():
        while True:
            data = await websocket.receive_json()
            with suppress(ValueError):
                _ = WSRequest.from_dict(data)
                invitations = await lobby_service.get_pending_invitations(user)
                response = PendingInvitationsResponse.create(invitations)
                await websocket.send_text(response)

    try:
        await websocket.accept()

        lobby = await lobby_service.get_user_lobby(user)
        response = CurrentLobbyResponse.create(lobby)
        await websocket.send_text(response)

        await receiver()

    except WebSocketDisconnect:
        connections_manager.remove(user.id)
