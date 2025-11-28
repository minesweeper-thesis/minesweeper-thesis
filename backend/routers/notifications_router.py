from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUserWebSocket
from backend.routers.schemas.lobby import (
    CurrentLobbyResponse,
    PendingInvitationsResponse,
)
from backend.routers.websockets.connections_manager import connections_manager

LobbyService = Annotated[services.LobbyService, Depends()]

notifications_router = APIRouter(tags=["notifications"])


@notifications_router.websocket("/ws")
async def send_notifications(
    websocket: WebSocket,
    user: CurrentUserWebSocket,
    lobby_service: LobbyService,
):
    """WebSocket endpoint for receiving game invitations."""
    connections_manager.add(user.id, websocket)

    async def receiver():
        while True:
            data = await websocket.receive_json()
            request_type = data.get("type")

            if request_type == "pending_invitations":
                invitations = lobby_service.lobby_repo.get_pending_invitations(user)
                response = PendingInvitationsResponse.from_core(invitations)
                await websocket.send_text(response.model_dump_json())

    try:
        await websocket.accept()

        lobby = await lobby_service.get_user_lobby(user)
        msg = CurrentLobbyResponse.from_core(lobby)
        await websocket.send_text(msg.model_dump_json())

        await receiver()

    except WebSocketDisconnect:
        connections_manager.remove(user.id)
