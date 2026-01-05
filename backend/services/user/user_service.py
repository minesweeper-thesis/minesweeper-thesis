import logging
from typing import Literal, Optional

from fastapi_pagination import Params

from backend.core.game.types import GameMode, GameResult, GameStatus
from backend.core.user import User
from backend.di.dependencies import *
from backend.services.exceptions import *

logger = logging.getLogger(__name__)


class UserService:
    def __init__(
        self,
        user_repo: UserRepositoryDep,
        singleplayer_repo: SingleplayerRepositoryDep,
    ):
        self.user_repo = user_repo
        self.singleplayer_repo = singleplayer_repo

    async def set_avatar(self, user: User, content: bytes) -> str:
        logger.debug(f"set_avatar(user_id={user.id}, content_size={len(content)})")
        user = await self.user_repo.set_avatar(user.id, content)
        assert user.avatar is not None
        logger.info(f"Avatar set for user {user.id}")
        return user.avatar.url

    async def delete_avatar(self, user: User) -> None:
        logger.debug(f"delete_avatar(user_id={user.id})")
        if user.avatar is not None:
            await self.user_repo.set_avatar(user.id, None)
            logger.info(f"Avatar deleted for user {user.id}")

    async def search_users(self, query: str, pagination_params: Params):
        logger.debug(f"search_users(query='{query}', page={pagination_params.page})")
        return await self.user_repo.search_users(query, pagination_params)

    async def get_gameplays(
        self,
        user: User,
        pagination_params: Params,
        status: Optional[GameStatus] = None,
        result: Optional[GameResult] = None,
        used_hints: Optional[bool] = None,
        min_time: Optional[float] = None,
        max_time: Optional[float] = None,
        mode: Optional[GameMode] = None,
        order_by: Optional[Literal["time_asc", "time_desc"]] = None,
    ):
        logger.debug(f"get_gameplays(user_id={user.id}, page={pagination_params.page})")
        return await self.singleplayer_repo.get_gameplays(
            user.id,
            pagination_params,
            status=status,
            result=result,
            used_hints=used_hints,
            min_time=min_time,
            max_time=max_time,
            mode=mode,
            order_by=order_by,
        )


__all__ = ["UserService"]
