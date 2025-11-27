import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_pagination import Params

from backend import services
from backend.lib.auth import CurrentUser
from backend.lib.connections_manager import connections_manager
from backend.lib.websockets_registry import multi_websockets
from backend.routers.schemas.serialize import create_response

from .schemas.lobby_schemas import *

PaginationParams = Annotated[Params, Depends()]

LobbyService = Annotated[services.LobbyService, Depends()]

lobby_router = APIRouter(prefix="/lobbies", tags=["lobby"])
invitations_router = APIRouter(prefix="/invitations", tags=["game-invitations"])


async def notify(receiver_id: uuid.UUID, data):
    if connections_manager.is_user_online(receiver_id):
        websocket = connections_manager.get(receiver_id)
        await websocket.send_text(create_response(data))


async def game_notify(receiver_id: uuid.UUID, data):
    if receiver_id in multi_websockets._websockets:
        websocket = multi_websockets.get(receiver_id)
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
    await service.update_lobby(lobby_id, user, config.to_dto(), notify)


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
    lobby, messages = await service.join_lobby(user, request.invitation_id, notify)
    return LobbyResponse.from_core(lobby, messages)


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


@lobby_router.post("/{lobby_id}/ready")
async def set_user_ready(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
):
    async def close_connection():
        if user.id in multi_websockets._websockets:
            await multi_websockets.get(user.id).close()

    service.on_session_end_callback = close_connection
    await service.set_user_ready(lobby_id, user, notify, game_notify)


@lobby_router.post("/{lobby_id}/cancel-ready")
async def set_user_not_ready(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    # service: LobbyService,
):
    """Sets the user as ready in the lobby."""
    # await service.set_user_not_ready(lobby_id, user, notify)


@lobby_router.post("/{lobby_id}/chat-messages")
async def send_chat_message(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyService,
    request: ChatMessageRequest,
):
    """Sends a chat message in the lobby."""
    await service.send_chat_message(lobby_id, user, request.content, notify)


@lobby_router.get("/{lobby_id}/chat-messages")
async def get_chat_messages(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyService,
    params: PaginationParams,
):
    """Retrieves chat messages from the lobby."""
    messages = await service.get_chat_messages(lobby_id, user, params)
    return [ChatMessageResponse.from_core(message) for message in messages]
