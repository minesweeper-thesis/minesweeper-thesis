import uuid
from typing import Annotated

import filetype
from fastapi import Depends
from fastapi_pagination import Params

import backend.repositories.exceptions as repo_exceptions
from backend import repositories
from backend.models import FriendRequest, FriendRequestStatus, Friendship
from backend.services.auth_service import CurrentUser
from backend.services.avatar import get_avatar_storage, storage
from backend.services.exceptions import *

UserRepository = Annotated[repositories.UserRepository, Depends()]
GameRepository = Annotated[repositories.GameRepository, Depends()]
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

    async def get_friends(self, pagination_params: Params):
        return await self.user_repo.get_friends(self.user.id, pagination_params)

    async def get_pending_friend_requests(self, pagination_params: Params):
        return await self.user_repo.get_friend_requests(
            pagination_params,
            friend_id=self.user.id,
            status=FriendRequestStatus.pending,
        )

    async def make_friend_request(self, friend_id: uuid.UUID):
        if self.user.id == friend_id:
            raise CannotFriendRequestYourself()

        existing_friendship = await self.user_repo.get_friendship(
            self.user.id, friend_id
        )
        if existing_friendship:
            raise UsersAlreadyFriends()

        friend_request = await self.user_repo.get_friend_request(
            user_id=self.user.id,
            friend_id=friend_id,
            status=FriendRequestStatus.pending,
        )
        if friend_request:
            raise FriendRequestAlreadySent()

        friend_request = FriendRequest(
            user_id=self.user.id,
            friend_id=friend_id,
            status=FriendRequestStatus.pending,
        )
        return await self.user_repo.add_friend_request(friend_request)

    async def accept_friend_request(self, friend_request_id: uuid.UUID):
        try:
            friend_request = await self.user_repo.get_friend_request(
                id=friend_request_id,
                friend_id=self.user.id,
                status=FriendRequestStatus.pending,
            )

            await self.user_repo.add_friendship(
                Friendship(
                    user_id=friend_request.user_id, friend_id=friend_request.friend_id
                )
            )
            await self.user_repo.add_friendship(
                Friendship(
                    user_id=friend_request.friend_id, friend_id=friend_request.user_id
                )
            )
            await self.user_repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.accepted
            )
        except repo_exceptions.FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def reject_friend_request(self, friend_request_id: uuid.UUID):
        try:
            friend_request = await self.user_repo.get_friend_request(
                id=friend_request_id,
                friend_id=self.user.id,
                status=FriendRequestStatus.pending,
            )

            await self.user_repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.rejected
            )
        except repo_exceptions.FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def remove_friend(self, friend_id: uuid.UUID):
        try:
            friendship1 = await self.user_repo.get_friendship(self.user.id, friend_id)
            friendship2 = await self.user_repo.get_friendship(friend_id, self.user.id)

            await self.user_repo.remove_friendship(friendship1)
            await self.user_repo.remove_friendship(friendship2)

        except repo_exceptions.FriendshipNotFound:
            raise UsersNotFriends() from None
