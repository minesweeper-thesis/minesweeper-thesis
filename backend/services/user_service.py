import uuid
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

import backend.repositories.exceptions as repo_exceptions
from backend.models import FriendRequest, FriendRequestStatus, Friendship, Gameplay
from backend.repositories import UserRepository
from backend.services.exceptions import *


class UserService:
    def __init__(self, repo: Annotated[UserRepository, Depends()]):
        self.repo = repo

    async def save_gameplay(
        self,
        user_id: uuid.UUID,
        board_id: uuid.UUID,
        time: float,
        used_prompts: bool,
        won: bool,
    ):
        gameplay = Gameplay(
            user_id=user_id,
            board_id=board_id,
            time=time,
            used_prompts=used_prompts,
            won=won,
        )
        await self.repo.add_gameplay(gameplay)

    async def get_gameplays(self, user_id: uuid.UUID, pagination_params: Params):
        return await self.repo.get_gameplays(user_id, pagination_params)

    async def get_friends(self, user_id: uuid.UUID, pagination_params: Params):
        return await self.repo.get_friends(user_id, pagination_params)

    async def get_pending_friend_requests(
        self, user_id: uuid.UUID, pagination_params: Params
    ):
        return await self.repo.get_friend_requests(
            pagination_params,
            friend_id=user_id,
            status=FriendRequestStatus.pending,
        )

    async def make_friend_request(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        if user_id == friend_id:
            raise CannotFriendRequestYourself()

        existing_friendship = await self.repo.get_friendship(user_id, friend_id)
        if existing_friendship:
            raise UsersAlreadyFriends()

        friend_request = await self.repo.get_friend_request(
            user_id=user_id, friend_id=friend_id, status=FriendRequestStatus.pending
        )
        if friend_request:
            raise FriendRequestAlreadySent()

        friend_request = FriendRequest(
            user_id=user_id, friend_id=friend_id, status=FriendRequestStatus.pending
        )
        return await self.repo.add_friend_request(friend_request)

    async def accept_friend_request(
        self, user_id: uuid.UUID, friend_request_id: uuid.UUID
    ):
        try:
            friend_request = await self.repo.get_friend_request(
                id=friend_request_id,
                friend_id=user_id,
                status=FriendRequestStatus.pending,
            )

            await self.repo.add_friendship(
                Friendship(
                    user_id=friend_request.user_id, friend_id=friend_request.friend_id
                )
            )
            await self.repo.add_friendship(
                Friendship(
                    user_id=friend_request.friend_id, friend_id=friend_request.user_id
                )
            )
            await self.repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.accepted
            )
        except repo_exceptions.FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def reject_friend_request(
        self, user_id: uuid.UUID, friend_request_id: uuid.UUID
    ):
        try:
            friend_request = await self.repo.get_friend_request(
                id=friend_request_id,
                friend_id=user_id,
                status=FriendRequestStatus.pending,
            )

            await self.repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.rejected
            )
        except repo_exceptions.FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def remove_friend(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        try:
            friendship1 = await self.repo.get_friendship(user_id, friend_id)
            friendship2 = await self.repo.get_friendship(friend_id, user_id)

            await self.repo.remove_friendship(friendship1)
            await self.repo.remove_friendship(friendship2)

        except repo_exceptions.FriendshipNotFound:
            raise UsersNotFriends() from None
