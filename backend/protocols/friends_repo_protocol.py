import uuid
from typing import Optional, Protocol

from fastapi_pagination import Page, Params

from backend.core.user import FriendRequest, FriendRequestStatus, Friendship, User


class FriendRequestNotFound(Exception):
    pass


class FriendshipNotFound(Exception):
    pass


class FriendsRepository(Protocol):
    async def get_friends(
        self, user_id: uuid.UUID, pagination_params: Params
    ) -> Page[User]: ...

    async def get_friend_request(
        self,
        id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        friend_id: Optional[uuid.UUID] = None,
        status: Optional[FriendRequestStatus] = None,
    ) -> FriendRequest: ...

    async def get_friend_requests(
        self,
        pagination_params: Params,
        user_id: Optional[uuid.UUID] = None,
        friend_id: Optional[uuid.UUID] = None,
        status: Optional[FriendRequestStatus] = None,
    ) -> Page[FriendRequest]: ...

    async def add_friend_request(self, friend_request: FriendRequest) -> None: ...

    async def change_friend_request_status(
        self, friend_request_id: uuid.UUID, status: FriendRequestStatus
    ) -> None: ...

    async def add_friendship(self, friendship: Friendship) -> None: ...

    async def get_friendship(
        self,
        user_id: uuid.UUID,
        friend_id: uuid.UUID,
    ) -> Friendship: ...

    async def remove_friendship(
        self, user_id: uuid.UUID, friend_id: uuid.UUID
    ) -> None: ...


__all__ = ["FriendsRepository"]
