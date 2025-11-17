from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories
from backend.lib.auth import CurrentUser
from backend.lib.avatar import get_avatar_storage, storage
from backend.services.exceptions import *

UserRepository = Annotated[repositories.UserRepository, Depends()]
GameRepository = Annotated[repositories.SingleplayerRepository, Depends()]
AvatarStorage = Annotated[storage.AvatarStorage, Depends(get_avatar_storage)]


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        user: CurrentUser,
        avatar_storage: AvatarStorage,
    ):
        self.user_repo = user_repo
        self.user = user
        self.avatar_storage = avatar_storage

    async def set_avatar(self, content: bytes) -> str:
        url = await self.avatar_storage.save(self.user.id, content)
        await self.user_repo.set_avatar_url(self.user.id, url)
        return url

    async def delete_avatar(self) -> None:
        if self.user.avatar is not None:
            await self.avatar_storage.delete(self.user.avatar.url)
            await self.user_repo.set_avatar_url(self.user.id, None)

    async def search_users(self, query: str, pagination_params: Params):
        return await self.user_repo.search_users(query, pagination_params)
