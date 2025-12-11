import uuid
from typing import Optional, Protocol

from fastapi_pagination import Page, Params

from backend.core.single.gameplay import SingleplayerGameplay


class SingleplayerRepository(Protocol):
    async def add_gameplay(
        self,
        gameplay: SingleplayerGameplay,
        board_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> None: ...

    async def get_gameplays(
        self, user_id: uuid.UUID, pagination_params: Params
    ) -> Page[SingleplayerGameplay]: ...

    async def get_gameplay_by_id(
        self, gameplay_id: uuid.UUID
    ) -> SingleplayerGameplay: ...

    async def update_gameplay(
        self, gameplay: SingleplayerGameplay
    ) -> SingleplayerGameplay: ...


__all__ = ["SingleplayerRepository"]
