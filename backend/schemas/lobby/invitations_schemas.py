import uuid
from typing import Literal, Self

from pydantic import BaseModel

from backend.core.lobby import *
from backend.schemas import Response
from backend.schemas.lobby.lobby_schemas import GameConfigResponse
from backend.schemas.user import UserResponse


class InviteUserToLobbyRequest(BaseModel):
    user_id: uuid.UUID


class InvitationLobbyResponse(BaseModel):
    id: uuid.UUID
    host: UserResponse
    game_config: GameConfigResponse

    @classmethod
    def build(cls, lobby: Lobby) -> Self:
        return cls(
            id=lobby.id,
            host=UserResponse.build(lobby.host),
            game_config=GameConfigResponse.build(lobby.game_config),
        )


class InvitationResponse(Response):
    ws_type: Literal["invitation"] = "invitation"
    id: uuid.UUID
    lobby: InvitationLobbyResponse

    @classmethod
    def build(cls, invitation: Invitation) -> Self:
        return cls(
            id=invitation.id,
            lobby=InvitationLobbyResponse.build(invitation.lobby),
        )


class InvitationAnswerResponse(Response):
    ws_type: Literal["invitation_response"] = "invitation_response"
    invitation: InvitationResponse
    response: Literal["accepted", "rejected"]

    @classmethod
    def build(cls, invitation_response: InvitationAnswer) -> Self:
        return cls(
            invitation=InvitationResponse.build(invitation_response.invitation),
            response=invitation_response.answer,
        )


class PendingInvitationsResponse(Response):
    ws_type: Literal["pending_invitations"] = "pending_invitations"
    invitations: list[InvitationResponse]

    @classmethod
    def build(cls, invitations: list[Invitation]) -> Self:
        return cls(
            invitations=[
                InvitationResponse.build(invitation) for invitation in invitations
            ],
        )


__all__ = [
    "InviteUserToLobbyRequest",
    "InvitationResponse",
    "InvitationAnswerResponse",
    "InvitationLobbyResponse",
    "PendingInvitationsResponse",
]
