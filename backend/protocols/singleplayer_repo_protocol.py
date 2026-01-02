import uuid
from typing import Literal, Optional, Protocol

from fastapi_pagination import Page, Params

from backend.core.game.types import GameMode, GameResult, GameStatus
from backend.core.single.single_gameplay import SingleplayerGameplay


class GameplayNotFound(Exception):
    pass


class SingleplayerRepository(Protocol):
    async def add_gameplay(
        self,
        gameplay: SingleplayerGameplay,
        board_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
    ) -> None: ...

    async def get_gameplays(
        self,
        user_id: uuid.UUID,
        pagination_params: Params,
        status: Optional[GameStatus] = None,
        result: Optional[GameResult] = None,
        used_hints: Optional[bool] = None,
        min_time: Optional[float] = None,
        max_time: Optional[float] = None,
        mode: Optional[GameMode] = None,
        order_by: Optional[Literal["time_asc", "time_desc"]] = None,
    ) -> Page[SingleplayerGameplay]: ...

    async def get_gameplay_by_id(
        self, gameplay_id: uuid.UUID
    ) -> SingleplayerGameplay: ...

    async def update_gameplay(
        self, gameplay: SingleplayerGameplay
    ) -> SingleplayerGameplay: ...

    async def get_user_gameplay_on_board(
        self, user_id: uuid.UUID, board_id: uuid.UUID
    ) -> SingleplayerGameplay: ...


__all__ = ["SingleplayerRepository"]
