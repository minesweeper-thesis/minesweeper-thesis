import uuid
from datetime import datetime, timedelta
from typing import Optional, Protocol

from fastapi_pagination import Page, Params

from backend.core.lobby import Invitation, Lobby, LobbyChatMessage


class LobbyRepository(Protocol):
    async def save_lobby(self, lobby: Lobby) -> None: ...

    async def get_lobby(self, lobby_id: uuid.UUID) -> Lobby: ...

    async def delete_lobby(self, lobby_id: uuid.UUID) -> None: ...

    async def save_invitation(self, invitation: Invitation, ttl: timedelta) -> None: ...

    async def get_invitation(self, invitation_id: uuid.UUID) -> Invitation: ...

    async def delete_invitation(self, invitation_id: uuid.UUID) -> None: ...

    async def get_pending_invitations(self, user_id: uuid.UUID) -> list[Invitation]: ...

    async def get_user_lobby(self, user_id: uuid.UUID) -> Optional[Lobby]: ...

    async def add_message(self, message: LobbyChatMessage) -> None: ...

    async def get_messages(
        self, lobby_id: uuid.UUID, pagination_params: Params
    ) -> Page: ...

    async def set_kick_at(
        self, user_id: uuid.UUID, lobby_id: uuid.UUID, kick_at: datetime | None
    ) -> None: ...


__all__ = ["LobbyRepository"]
