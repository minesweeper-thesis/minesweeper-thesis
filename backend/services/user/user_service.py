import logging

from fastapi_pagination import Params

logger = logging.getLogger(__name__)

from backend.di.dependencies import *
from backend.lib.auth import CurrentUser
from backend.services.exceptions import *


class UserService:
    def __init__(
        self,
        user_repo: UserRepositoryDep,
        singleplayer_repo: SingleplayerRepositoryDep,
        user: CurrentUser,
    ):
        self.user_repo = user_repo
        self.singleplayer_repo = singleplayer_repo
        self.user = user

    async def set_avatar(self, content: bytes) -> str:
        logger.debug(f"set_avatar(user_id={self.user.id}, content_size={len(content)})")
        user = await self.user_repo.set_avatar(self.user.id, content)
        assert user.avatar is not None
        logger.info(f"Avatar set for user {self.user.id}")
        return user.avatar.url

    async def delete_avatar(self) -> None:
        logger.debug(f"delete_avatar(user_id={self.user.id})")
        if self.user.avatar is not None:
            await self.user_repo.set_avatar(self.user.id, None)
            logger.info(f"Avatar deleted for user {self.user.id}")

    async def search_users(self, query: str, pagination_params: Params):
        logger.debug(f"search_users(query='{query}', page={pagination_params.page})")
        return await self.user_repo.search_users(query, pagination_params)

    async def get_gameplays(self, pagination_params: Params):
        logger.debug(
            f"get_gameplays(user_id={self.user.id}, page={pagination_params.page})"
        )
        return await self.singleplayer_repo.get_gameplays(
            self.user.id, pagination_params
        )


__all__ = ["UserService"]
