from fastapi_pagination import Params

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
        user = await self.user_repo.set_avatar(self.user.id, content)
        assert user.avatar is not None
        return user.avatar.url

    async def delete_avatar(self) -> None:
        if self.user.avatar is not None:
            await self.user_repo.set_avatar(self.user.id, None)

    async def search_users(self, query: str, pagination_params: Params):
        return await self.user_repo.search_users(query, pagination_params)

    async def get_gameplays(self, pagination_params: Params):
        return await self.singleplayer_repo.get_gameplays(
            self.user.id, pagination_params
        )


__all__ = ["UserService"]
