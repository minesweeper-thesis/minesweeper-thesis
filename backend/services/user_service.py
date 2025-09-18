import uuid
from typing import Annotated

from fastapi import Depends
from fastapi_pagination import Params

from backend.models import FriendRequest, FriendRequestStatus, Friendship, Gameplay
from backend.repositories import UserRepository


class UserService:
    def __init__(self, repo: Annotated[UserRepository, Depends()]):
        self.repo = repo

    async def save_gameplay(
        self,
        user_id: uuid.UUID,
        board_id: uuid.UUID,
        score: float,
        time: float,
        used_prompts: bool,
    ):
        gameplay = Gameplay(
            user_id=user_id,
            board_id=board_id,
            score=score,
            time=time,
            used_prompts=used_prompts,
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
            friend_id=user_id,
            status=FriendRequestStatus.pending,
            pagination_params=pagination_params,
        )

    async def make_friend_request(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        if user_id == friend_id:
            raise ValueError("Cannot make friend request to yourself")

        existing_friendship = await self.repo.get_friendship(user_id, friend_id)
        if existing_friendship:
            raise ValueError("Friendship already exists")

        friend_request = await self.repo.get_friend_requests(
            user_id=user_id, friend_id=friend_id, status=FriendRequestStatus.pending
        )
        if friend_request:
            raise ValueError("Friend request already sent")

        friend_request = FriendRequest(
            user_id=user_id, friend_id=friend_id, status=FriendRequestStatus.pending
        )
        return await self.repo.add_friend_request(friend_request)

    async def accept_friend_request(
        self, user_id: uuid.UUID, friend_request_id: uuid.UUID
    ):
        friend_requests = await self.repo.get_friend_requests(
            id=friend_request_id,
            friend_id=user_id,
            status=FriendRequestStatus.pending,
        )

        if not len(friend_requests):
            raise ValueError("No pending friend request found")

        friend_request = friend_requests[0]

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
            friend_request_id, FriendRequestStatus.accepted
        )

    async def reject_friend_request(
        self, user_id: uuid.UUID, friend_request_id: uuid.UUID
    ):
        friend_requests = await self.repo.get_friend_requests(
            id=friend_request_id,
            friend_id=user_id,
            status=FriendRequestStatus.pending,
        )
        if not len(friend_requests):
            raise ValueError("No pending friend request found")

        await self.repo.change_friend_request_status(
            friend_request_id, FriendRequestStatus.rejected
        )

    async def remove_friend(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        friendship1 = await self.repo.get_friendship(user_id, friend_id)
        friendship2 = await self.repo.get_friendship(friend_id, user_id)

        if friendship1:
            await self.repo.remove_friendship(friendship1)
        if friendship2:
            await self.repo.remove_friendship(friendship2)
