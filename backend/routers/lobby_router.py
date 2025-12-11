import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, Params

from backend import services
from backend.lib.auth import CurrentUser
from backend.schemas.lobby import *

PaginationParams = Annotated[Params, Depends()]

LobbyService = Annotated[services.LobbyService, Depends()]
LobbyChatService = Annotated[services.LobbyChatService, Depends()]
LobbyInvitationService = Annotated[services.LobbyInvitationService, Depends()]
LobbyReadyService = Annotated[services.LobbyReadyService, Depends()]

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
    service: LobbyInvitationService,
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
    lobby = await service.join_lobby(user, request.invitation_id)
    return LobbyResponse.build(lobby)


@lobby_router.post("/{lobby_id}/leave")
async def leave_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
):
    """Leaves the lobby or removes a member."""
    await service.remove_user_from_lobby(lobby_id, user)


@lobby_router.post("/{lobby_id}/kick")
async def kick_user_from_lobby(
    lobby_id: uuid.UUID,
    service: LobbyService,
    user: CurrentUser,
    request: KickUserRequest,
):
    """Kicks a user from the lobby."""
    await service.kick_from_lobby(lobby_id, user, request.user_id)


@invitations_router.delete("/{invitation_id}")
async def reject_game_invitation(
    user: CurrentUser,
    service: LobbyInvitationService,
    invitation_id: uuid.UUID,
):
    """Rejects a game invitation."""
    await service.reject_game_invitation(invitation_id, user)


@lobby_router.post("/{lobby_id}/ready/set")
async def set_user_ready(
    lobby_id: uuid.UUID,
    service: LobbyReadyService,
    user: CurrentUser,
):
    """Sets the user as ready in the lobby."""
    await service.set_user_ready_in_lobby(lobby_id, user)


@lobby_router.post("/{lobby_id}/ready/cancel")
async def cancel_user_ready(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyReadyService,
):
    """Sets the user as not ready in the lobby."""
    await service.cancel_user_ready_in_lobby(lobby_id, user)


@lobby_router.post("/{lobby_id}/ready/toggle")
async def toggle_user_ready(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyReadyService,
):
    await service.toggle_user_ready_in_lobby(lobby_id, user)


@lobby_router.post("/{lobby_id}/chat-messages")
async def send_chat_message(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyChatService,
    request: LobbyChatMessageRequest,
):
    """Sends a chat message in the lobby."""
    await service.send_chat_message(lobby_id, user, request.content)


@lobby_router.get(
    "/{lobby_id}/chat-messages",
    responses={200: {"model": Page[LobbyChatMessageResponse]}},
)
async def get_chat_messages(
    lobby_id: uuid.UUID,
    user: CurrentUser,
    service: LobbyChatService,
    pagination_params: PaginationParams,
):
    """Retrieves chat messages from the lobby."""
    page = await service.get_chat_messages(lobby_id, user, pagination_params)
    page.items = [LobbyChatMessageResponse.build(message) for message in page.items]
    return page
