import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

import backend.repositories.exceptions as repo_exceptions
from backend import repositories
from backend.core.user import FriendRequest, FriendRequestStatus, Friendship
from backend.lib.auth import CurrentUser
from backend.services.exceptions import *

FriendsRepository = Annotated[repositories.FriendsRepository, Depends()]


class FriendsService:
    def __init__(
        self,
        friends_repo: FriendsRepository,
        user_repo: Annotated[repositories.UserRepository, Depends()],
        user: CurrentUser,
    ):
        self.friends_repo = friends_repo
        self.user_repo = user_repo
        self.user = user

    async def get_friends(self, pagination_params: Params):
        return await self.friends_repo.get_friends(self.user.id, pagination_params)

    async def get_pending_friend_requests(self, pagination_params: Params):
        return await self.friends_repo.get_friend_requests(
            pagination_params,
            friend_id=self.user.id,
            status=FriendRequestStatus.pending,
        )

    async def get_sent_friend_requests(self, pagination_params: Params):
        return await self.friends_repo.get_friend_requests(
            pagination_params,
            user_id=self.user.id,
            status=FriendRequestStatus.pending,
        )

    async def _check_if_requested_friend_exists(self, friend_id: uuid.UUID):
        try:
            await self.user_repo.get_user(friend_id)
        except repo_exceptions.UserNotFound:
            raise RequestedFriendNotExists() from None

    async def make_friend_request(self, friend_id: uuid.UUID):
        if self.user.id == friend_id:
            raise CannotFriendRequestYourself()

        await self._check_if_requested_friend_exists(friend_id)

        with suppress(repo_exceptions.FriendshipNotFound):
            existing_friendship = await self.friends_repo.get_friendship(
                self.user.id, friend_id
            )
            if existing_friendship:
                raise UsersAlreadyFriends()

        with suppress(repo_exceptions.FriendRequestNotFound):
            friend_request = await self.friends_repo.get_friend_request(
                user_id=self.user.id,
                friend_id=friend_id,
                status=FriendRequestStatus.pending,
            )
            if friend_request:
                raise FriendRequestAlreadySent()

        friend = await self.user_repo.get_user(friend_id)
        friend_request = FriendRequest(
            id=uuid.uuid4(),
            user=self.user,
            friend=friend,
            status=FriendRequestStatus.pending,
        )
        await self.friends_repo.add_friend_request(friend_request)

        return friend_request

    async def accept_friend_request(self, friend_request_id: uuid.UUID):
        try:
            friend_request = await self.friends_repo.get_friend_request(
                id=friend_request_id,
                friend_id=self.user.id,
                status=FriendRequestStatus.pending,
            )

            await self.friends_repo.add_friendship(
                Friendship(user=friend_request.user, friend=friend_request.friend)
            )
            await self.friends_repo.add_friendship(
                Friendship(user=friend_request.friend, friend=friend_request.user)
            )
            await self.friends_repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.accepted
            )
        except repo_exceptions.FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def reject_friend_request(self, friend_request_id: uuid.UUID):
        try:
            friend_request = await self.friends_repo.get_friend_request(
                id=friend_request_id,
                friend_id=self.user.id,
                status=FriendRequestStatus.pending,
            )

            await self.friends_repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.rejected
            )
        except repo_exceptions.FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def remove_friend(self, friend_id: uuid.UUID):
        try:
            await self.friends_repo.remove_friendship(self.user.id, friend_id)
            await self.friends_repo.remove_friendship(friend_id, self.user.id)

        except repo_exceptions.FriendshipNotFound:
            raise UsersNotFriends() from None
