import uuid
from typing import ClassVar, Literal, Self

from pydantic import BaseModel

from backend.core.lobby import *
from backend.routers.schemas import Response

from ..user_schemas import UserResponse


class InviteUserToLobbyRequest(BaseModel):
    user_id: uuid.UUID


class JoinLobbyRequest(BaseModel):
    invitation_id: uuid.UUID


class PendingInvitationsRequest(BaseModel):
    type: ClassVar[Literal["pending_invitations"]] = "pending_invitations"


class InvitationLobbyResponse(Response):
    id: uuid.UUID
    host: UserResponse
    game_config: GameConfig

    @classmethod
    def from_core(cls, lobby) -> Self:
        return cls(
            id=lobby.id,
            host=UserResponse.from_core(lobby.host),
            game_config=lobby.game_settings,
        )


class InvitationResponse(Response):
    ws_type: Literal["invitation"] = "invitation"
    id: uuid.UUID
    lobby: InvitationLobbyResponse

    @classmethod
    def from_core(cls, invitation: Invitation) -> Self:
        return cls(
            id=invitation.id,
            lobby=InvitationLobbyResponse.from_core(invitation.lobby),
        )


class InvitationAnswerResponse(Response):
    ws_type: Literal["invitation_response"] = "invitation_response"
    invitation: InvitationResponse
    response: Literal["accepted", "rejected"]

    @classmethod
    def from_core(cls, invitation_response: InvitationAnswer) -> Self:
        return cls(
            invitation=InvitationResponse.from_core(invitation_response.invitation),
            response=invitation_response.answer,
        )


class PendingInvitationsResponse(Response):
    ws_type: Literal["pending_invitations"] = "pending_invitations"
    invitations: list[InvitationResponse]

    @classmethod
    def from_core(cls, invitations: list[Invitation]) -> Self:
        return cls(
            invitations=[
                InvitationResponse.from_core(invitation) for invitation in invitations
            ],
        )


__all__ = [
    "InviteUserToLobbyRequest",
    "JoinLobbyRequest",
    "InvitationResponse",
    "InvitationAnswerResponse",
    "InvitationLobbyResponse",
    "PendingInvitationsResponse",
]
