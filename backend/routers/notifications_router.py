import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUserWebSocket
from backend.lib.connections_manager import ConnectionsManager

from .schemas.lobby_schemas import *

LobbyService = Annotated[services.LobbyService, Depends()]

notifications_router = APIRouter(tags=["notifications"])


@notifications_router.websocket("/ws")
async def send_notifications(
    websocket: WebSocket,
    user: CurrentUserWebSocket,
):
    """WebSocket endpoint for receiving game invitations."""
    ConnectionsManager.add_user(user.id, websocket)

    try:
        await websocket.accept()
        while True:
            await asyncio.sleep(5)
    except WebSocketDisconnect:
        ConnectionsManager.remove_user(user.id)
