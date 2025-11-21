import uuid
from abc import ABC, abstractmethod
from typing import ClassVar, Literal, Self

from pydantic import BaseModel

from backend.core.lobby import *
from backend.services.lobby_service import GameConfigUpdated, UserConnectionUpdated

from .user_schemas import UserResponse


class InviteUserToLobbyRequest(BaseModel):
    user_id: uuid.UUID


class JoinLobbyRequest(BaseModel):
    invitation_id: uuid.UUID


class PendingInvitationsRequest(BaseModel):
    type: ClassVar[Literal["pending_invitations"]] = "pending_invitations"


class DifficultyLevelRequest(BaseModel):
    rows: int
    columns: int
    mine_count: int


class UpdateGameConfigRequest(BaseModel):
    difficulty_level: DifficultyLevelRequest
    game_mode: GameMode
    generator_type: GeneratorType
    generator_settings: Optional[GeneratorSettings] = None


class Response(ABC, BaseModel):
    @classmethod
    @abstractmethod
    def from_core(cls, data) -> Self:
        """Create response from domain object."""
        ...


class GameConfigUpdatedResponse(Response):
    type: Literal["game_config_updated"] = "game_config_updated"
    lobby_id: uuid.UUID
    game_config: GameConfig

    @classmethod
    def from_core(cls, data: GameConfigUpdated) -> Self:
        return cls(lobby_id=data.lobby_id, game_config=data.game_config)


class InvitationLobbyResponse(Response):
    id: uuid.UUID
    host: UserResponse
    game_config: GameConfig

    @classmethod
    def from_core(cls, lobby) -> Self:
        return cls(
            id=lobby.id,
            host=UserResponse.from_user(lobby.host),
            game_config=lobby.game_settings,
        )


class LobbyResponse(Response):
    id: uuid.UUID
    host: UserResponse
    users: list[UserResponse]
    game_config: GameConfig

    @classmethod
    def from_core(cls, lobby: Lobby) -> Self:
        return cls(
            id=lobby.id,
            host=UserResponse.from_user(lobby.host),
            users=[UserResponse.from_user(user) for user in lobby.users],
            game_config=lobby.game_config,
        )


class InvitationResponse(Response):
    type: Literal["invitation"] = "invitation"
    id: uuid.UUID
    lobby: InvitationLobbyResponse

    @classmethod
    def from_core(cls, invitation: Invitation) -> Self:
        return cls(
            id=invitation.id,
            lobby=InvitationLobbyResponse.from_core(invitation.lobby),
        )


class InvitationAnswerResponse(Response):
    type: Literal["invitation_response"] = "invitation_response"
    invitation: InvitationResponse
    response: Literal["accepted", "rejected"]

    @classmethod
    def from_core(cls, invitation_response: InvitationAnswer) -> Self:
        return cls(
            invitation=InvitationResponse.from_core(invitation_response.invitation),
            response=invitation_response.answer,
        )


class UserConnectionStatusResponse(Response):
    type: Literal["user_connection_status"] = "user_connection_status"
    lobby_id: uuid.UUID
    user: UserResponse
    status: Literal["connected", "disconnected"]

    @classmethod
    def from_core(cls, data: UserConnectionUpdated) -> Self:
        return cls(
            lobby_id=data.lobby_id,
            user=UserResponse.from_user(data.user),
            status=data.status,
        )


class PendingInvitationsResponse(Response):
    type: Literal["pending_invitations"] = "pending_invitations"
    invitations: list[InvitationResponse]

    @classmethod
    def from_core(cls, invitations: list[Invitation]) -> Self:
        return cls(
            invitations=[
                InvitationResponse.from_core(invitation) for invitation in invitations
            ],
        )


class CurrentLobbyResponse(Response):
    type: Literal["current_lobby"] = "current_lobby"
    lobby: Optional[LobbyResponse]

    @classmethod
    def from_core(cls, lobby: Optional[Lobby]) -> Self:
        return cls(
            lobby=LobbyResponse.from_core(lobby) if lobby else None,
        )
