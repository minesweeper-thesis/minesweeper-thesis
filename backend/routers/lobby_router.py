import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from backend import services
from backend.lib.auth import CurrentUser
from backend.lib.connections_manager import ConnectionsManager
from backend.routers.schemas import create_response
from backend.services.lobby_service import NewGameConfig

from .schemas.lobby_schemas import *

LobbyService = Annotated[services.LobbyService, Depends()]

lobby_router = APIRouter(prefix="/lobbies", tags=["lobby"])
invitations_router = APIRouter(prefix="/invitations", tags=["game-invitations"])


async def notify(receiver_id: uuid.UUID, data):
    if ConnectionsManager.is_user_online(receiver_id):
        websocket = ConnectionsManager.get(receiver_id)
        await websocket.send_text(create_response(data))


@lobby_router.post("")
async def create_lobby(
    user: CurrentUser,
    service: LobbyService,
) -> LobbyResponse:
    """Creates a new lobby."""
    lobby = await service.create_lobby(user)
    return LobbyResponse.from_core(lobby)


@lobby_router.put("/{lobby_id}")
async def update_lobby_config(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    config: UpdateGameConfigRequest,
):
    """Updates lobby configuration."""
    await service.update_lobby(
        lobby_id, user, NewGameConfig(**config.model_dump()), notify
    )


@lobby_router.post("/{lobby_id}/invitations")
async def invite_user_to_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    request: InviteUserToLobbyRequest,
):
    """Sends an invitation to join the lobby."""
    await service.invite_to_lobby(lobby_id, user, request.user_id, notify)


@lobby_router.post("/{lobby_id}/join")
async def join_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    request: JoinLobbyRequest,
):
    """Joins a lobby using an invitation."""
    lobby = await service.join_lobby(user, request.invitation_id, notify)
    return LobbyResponse.from_core(lobby)


@lobby_router.post("/{lobby_id}/leave")
async def leave_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
):
    """Leaves the lobby or removes a member."""
    await service.remove_user_from_lobby(lobby_id, user, notify)


@invitations_router.delete("/{invitation_id}")
async def reject_game_invitation(
    user: CurrentUser,
    service: LobbyService,
    invitation_id: uuid.UUID,
):
    """Rejects a game invitation."""
    await service.reject_game_invitation(invitation_id, user, notify)
