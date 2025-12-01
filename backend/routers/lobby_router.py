import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_pagination import Params

from backend import services
from backend.lib.auth import CurrentUser
from backend.routers.schemas.lobby import *

PaginationParams = Annotated[Params, Depends()]

LobbyService = Annotated[services.LobbyService, Depends()]
CreateMultiplayerSessionUseCase = Annotated[
    services.CreateMultiplayerSessionUseCase, Depends()
]

lobby_router = APIRouter(prefix="/lobbies", tags=["lobby"])
invitations_router = APIRouter(prefix="/invitations", tags=["game-invitations"])


@lobby_router.post("")
async def create_lobby(
    user: CurrentUser,
    service: LobbyService,
) -> LobbyResponse:
    """Creates a new lobby."""
    lobby = await service.create_lobby(user)
    return LobbyResponse.build(lobby)


@lobby_router.put("/{lobby_id}")
async def update_lobby_config(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    config: UpdateGameConfigRequest,
):
    """Updates lobby configuration."""
    await service.update_lobby(lobby_id, user, config.to_dto())


@lobby_router.post("/{lobby_id}/invitations")
async def invite_user_to_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    request: InviteUserToLobbyRequest,
):
    """Sends an invitation to join the lobby."""
    await service.invite_to_lobby(lobby_id, user, request.user_id)


@lobby_router.post("/{lobby_id}/join")
async def join_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    request: JoinLobbyRequest,
):
    """Joins a lobby using an invitation."""
    lobby, messages = await service.join_lobby(user, request.invitation_id)
    return LobbyResponse.build(lobby, messages)


@lobby_router.post("/{lobby_id}/leave")
async def leave_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
):
    """Leaves the lobby or removes a member."""
    await service.remove_user_from_lobby(lobby_id, user)


@invitations_router.delete("/{invitation_id}")
async def reject_game_invitation(
    user: CurrentUser,
    service: LobbyService,
    invitation_id: uuid.UUID,
):
    """Rejects a game invitation."""
    await service.reject_game_invitation(invitation_id, user)


@lobby_router.post("/{lobby_id}/ready")
async def set_user_ready(
    lobby_id: uuid.UUID,
    service: CreateMultiplayerSessionUseCase,
    user: CurrentUser,
):
    await service.set_user_ready_in_lobby(lobby_id, user)


@lobby_router.post("/{lobby_id}/cancel-ready")
async def set_user_not_ready(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    # service: LobbyService,
):
    """Sets the user as ready in the lobby."""
    # await service.set_user_not_ready(lobby_id, user)


@lobby_router.post("/{lobby_id}/chat-messages")
async def send_chat_message(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyService,
    request: ChatMessageRequest,
):
    """Sends a chat message in the lobby."""
    await service.send_chat_message(lobby_id, user, request.content)


@lobby_router.get("/{lobby_id}/chat-messages")
async def get_chat_messages(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyService,
    pagination_params: PaginationParams,
):
    """Retrieves chat messages from the lobby."""
    messages = await service.get_chat_messages(lobby_id, user, pagination_params)
    return [ChatMessageResponse.build(message) for message in messages]
