import uuid
from typing import ClassVar, Literal

from pydantic import BaseModel

from backend.core.lobby import *
from backend.services.lobby_service import GameConfigUpdated, UserConnectionUpdated

from .user_schemas import UserResponse


class UpdateGameConfigRequest(BaseModel):
    game_config: GameConfig


class GameConfigUpdatedResponse(BaseModel):
    type: ClassVar[Literal["game_config_updated"]] = "game_config_updated"
    lobby_id: uuid.UUID
    game_config: GameConfig

    @staticmethod
    def create(data: GameConfigUpdated) -> "GameConfigUpdatedResponse":
        return GameConfigUpdatedResponse(
            lobby_id=data.lobby_id, game_config=data.game_config
        )


class InvitationLobbyResponse(BaseModel):
    id: uuid.UUID
    host: UserResponse
    game_config: GameConfig

    @staticmethod
    def create(lobby) -> "InvitationLobbyResponse":
        return InvitationLobbyResponse(
            id=lobby.id,
            host=UserResponse.from_user(lobby.host),
            game_config=lobby.game_settings,
        )


class LobbyResponse(BaseModel):
    id: uuid.UUID
    host: UserResponse
    users: list[UserResponse]
    game_config: GameConfig

    @staticmethod
    def create(lobby: Lobby) -> "LobbyResponse":
        return LobbyResponse(
            id=lobby.id,
            host=UserResponse.from_user(lobby.host),
            users=[UserResponse.from_user(user) for user in lobby.users],
            game_config=lobby.game_settings,
        )


class InvitationResponse(BaseModel):
    type: ClassVar[Literal["invitation"]] = "invitation"
    id: uuid.UUID
    lobby: InvitationLobbyResponse

    @staticmethod
    def create(invitation: Invitation) -> "InvitationResponse":
        return InvitationResponse(
            id=invitation.id,
            lobby=InvitationLobbyResponse.create(invitation.lobby),
        )


class InvitationAnswerResponse(BaseModel):
    type: ClassVar[Literal["invitation_response"]] = "invitation_response"
    invitation: InvitationResponse
    response: Literal["accepted", "rejected"]

    @staticmethod
    def create(
        invitation_response: InvitationAnswer,
    ) -> "InvitationAnswerResponse":
        return InvitationAnswerResponse(
            invitation=InvitationResponse.create(invitation_response.invitation),
            response=invitation_response.answer,
        )


class UserConnectionStatusResponse(BaseModel):
    type: ClassVar[Literal["user_connection_status"]] = "user_connection_status"
    lobby_id: uuid.UUID
    user: UserResponse
    status: Literal["connected", "disconnected"]

    @staticmethod
    def create(
        data: UserConnectionUpdated,
    ) -> "UserConnectionStatusResponse":
        return UserConnectionStatusResponse(
            lobby_id=data.lobby_id,
            user=UserResponse.from_user(data.user),
            status=data.status,
        )
