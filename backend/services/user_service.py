from typing import Annotated

import filetype
from fastapi import Depends
from fastapi_pagination import Params

from backend import repositories
from backend.lib.auth import CurrentUser
from backend.services.avatar import get_avatar_storage, storage
from backend.services.exceptions import *

UserRepository = Annotated[repositories.UserRepository, Depends()]
GameRepository = Annotated[repositories.SingleplayerRepository, Depends()]
AvatarStorage = Annotated[storage.AvatarStorage, Depends(get_avatar_storage)]


def add_file_extension(filename: str, content: bytes) -> str:
    kind = filetype.guess(content)

    if kind is None:
        raise ValueError("Invalid file content type")

    ext = kind.extension
    if not filename.lower().endswith(f".{ext}"):
        filename = f"{filename}.{ext}"

    return filename


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
        filename = add_file_extension(str(self.user.id), content)
        url = await self.avatar_storage.save(filename, content)
        await self.user_repo.set_avatar_url(self.user.id, url)
        return url

    async def delete_avatar(self) -> None:
        if self.user.avatar_url is not None:
            filename = self.user.avatar_url.split("/")[-1]

            await self.avatar_storage.delete(filename)
            await self.user_repo.set_avatar_url(self.user.id, None)

    async def search_users(self, query: str, pagination_params: Params):
        return await self.user_repo.search_users(query, pagination_params)
