import uuid
from typing import ClassVar, Literal, Self

from pydantic import BaseModel

from backend.core.lobby import *
from backend.routers.schemas import Response
from backend.services.lobby_service import (
    GameConfigUpdated,
    NewGameConfig,
    UserConnectionUpdated,
)

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
    rounds: int
    max_round_time: int
    difficulty_level: DifficultyLevelRequest
    game_mode: GameMode
    generator_type: GeneratorType
    generator_settings: Optional[GeneratorSettings] = None

    def to_dto(self) -> NewGameConfig:
        return NewGameConfig(
            rounds=self.rounds,
            max_round_time=self.max_round_time,
            difficulty_level=DifficultyLevel(
                rows=self.difficulty_level.rows,
                columns=self.difficulty_level.columns,
                mine_count=self.difficulty_level.mine_count,
            ),
            game_mode=self.game_mode,
            generator_type=self.generator_type,
            generator_settings=self.generator_settings,
        )


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
    def from_core(cls, lobby: Lobby) -> Self:
        return cls(
            id=lobby.id,
            host=UserResponse.from_user(lobby.host),
            game_config=lobby.game_config,
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


__all__ = [
    "InviteUserToLobbyRequest",
    "JoinLobbyRequest",
    "UpdateGameConfigRequest",
    "LobbyResponse",
    "InvitationResponse",
    "InvitationAnswerResponse",
    "GameConfigUpdatedResponse",
    "InvitationLobbyResponse",
    "UserConnectionStatusResponse",
    "PendingInvitationsResponse",
    "CurrentLobbyResponse",
    "GameConfigUpdatedResponse",
]
