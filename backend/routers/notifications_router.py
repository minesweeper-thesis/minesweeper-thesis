from contextlib import suppress
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from backend import services
from backend.lib.auth import CurrentUserWebSocket
from backend.lib.notification_system import get_notification_system
from backend.routers.schemas import WSRequest
from backend.routers.schemas.lobby import PendingInvitationsResponse

UserConnectionService = Annotated[services.UserConnectionService, Depends()]
LobbyInvitationService = Annotated[services.LobbyInvitationService, Depends()]

notifications_router = APIRouter(tags=["notifications"])


@notifications_router.websocket("/ws")
async def send_notifications(
    websocket: WebSocket,
    user: CurrentUserWebSocket,
    user_connection_service: UserConnectionService,
    lobby_invitation_service: LobbyInvitationService,
):
    notification_system = get_notification_system()

    async def receiver():
        while True:
            data = await websocket.receive_json()
            with suppress(ValueError):
                _ = WSRequest.from_dict(data)
                invitations = await lobby_invitation_service.get_pending_invitations(
                    user
                )
                response = PendingInvitationsResponse.create(invitations)
                await websocket.send_text(response)

    try:
        await websocket.accept()

        notification_system.connect_user(user.id, websocket)
        await user_connection_service.set_user_online(user)

        await receiver()

    except WebSocketDisconnect:
        notification_system.disconnect_user(user.id)
        await user_connection_service.set_user_offline(user)
