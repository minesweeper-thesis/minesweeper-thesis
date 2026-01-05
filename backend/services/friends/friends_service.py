import logging
import uuid
from contextlib import suppress

from fastapi_pagination import Params

from backend.core.user import FriendRequest, FriendRequestStatus, Friendship, User
from backend.di.dependencies import (
    FriendsRepositoryDep,
    NotificationSystemDep,
    UserRepositoryDep,
)
from backend.protocols.repos.exceptions import (
    FriendRequestNotFound,
    FriendshipNotFound,
    UserNotFound,
)
from backend.services.exceptions import *

logger = logging.getLogger(__name__)


class FriendsService:
    def __init__(
        self,
        friends_repo: FriendsRepositoryDep,
        user_repo: UserRepositoryDep,
        notification_system: NotificationSystemDep,
    ):
        self.friends_repo = friends_repo
        self.user_repo = user_repo
        self.notification_system = notification_system

    async def get_friends(self, user: User, pagination_params: Params):
        logger.debug(f"get_friends(user_id={user.id}, page={pagination_params.page})")
        return await self.friends_repo.get_friends(user.id, pagination_params)

    async def get_pending_friend_requests(self, user: User, pagination_params: Params):
        logger.debug(f"get_pending_friend_requests(user_id={user.id})")
        return await self.friends_repo.get_friend_requests(
            pagination_params,
            friend_id=user.id,
            status=FriendRequestStatus.pending,
        )

    async def get_sent_friend_requests(self, user: User, pagination_params: Params):
        logger.debug(f"get_sent_friend_requests(user_id={user.id})")
        return await self.friends_repo.get_friend_requests(
            pagination_params,
            user_id=user.id,
            status=FriendRequestStatus.pending,
        )

    async def _check_if_requested_friend_exists(self, friend_id: uuid.UUID):
        try:
            await self.user_repo.get_user(friend_id)
        except UserNotFound:
            raise RequestedFriendNotExists() from None

    async def make_friend_request(self, user: User, friend_id: uuid.UUID):
        logger.debug(f"make_friend_request(user_id={user.id}, friend_id={friend_id})")
        if user.id == friend_id:
            raise CannotFriendRequestYourself()

        await self._check_if_requested_friend_exists(friend_id)

        with suppress(FriendshipNotFound):
            existing_friendship = await self.friends_repo.get_friendship(
                user.id,
                friend_id,
            )
            if existing_friendship:
                raise UsersAlreadyFriends()

        with suppress(FriendRequestNotFound):
            friend_request = await self.friends_repo.get_friend_request(
                user_id=user.id,
                friend_id=friend_id,
                status=FriendRequestStatus.pending,
            )
            if friend_request:
                raise FriendRequestAlreadySent()

        friend = await self.user_repo.get_user(friend_id)
        friend_request = FriendRequest(
            id=uuid.uuid4(),
            user=user,
            friend=friend,
            status=FriendRequestStatus.pending,
        )
        await self.friends_repo.add_friend_request(friend_request)

        await self.notification_system.notify(friend_id, friend_request)

        logger.info(f"Friend request sent from {user.id} to {friend_id}")
        return friend_request

    async def accept_friend_request(self, user: User, friend_request_id: uuid.UUID):
        try:
            friend_request = await self.friends_repo.get_friend_request(
                id=friend_request_id,
                friend_id=user.id,
                status=FriendRequestStatus.pending,
            )

            await self.friends_repo.add_friendship(
                Friendship(user=friend_request.user, friend=friend_request.friend)
            )
            await self.friends_repo.add_friendship(
                Friendship(user=friend_request.friend, friend=friend_request.user)
            )

            friend_request.status = FriendRequestStatus.accepted
            await self.friends_repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.accepted
            )

            await self.notification_system.notify(
                friend_request.user.id, friend_request
            )
        except FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def reject_friend_request(self, user: User, friend_request_id: uuid.UUID):
        try:
            friend_request = await self.friends_repo.get_friend_request(
                id=friend_request_id,
                friend_id=user.id,
                status=FriendRequestStatus.pending,
            )

            friend_request.status = FriendRequestStatus.rejected
            await self.friends_repo.change_friend_request_status(
                friend_request.id, FriendRequestStatus.rejected
            )

            await self.notification_system.notify(
                friend_request.user.id, friend_request
            )
        except FriendRequestNotFound:
            raise FriendRequestNotExists() from None

    async def remove_friend(self, user: User, friend_id: uuid.UUID):
        try:
            await self.friends_repo.remove_friendship(user.id, friend_id)
            await self.friends_repo.remove_friendship(friend_id, user.id)

        except FriendshipNotFound:
            raise UsersNotFriends() from None


__all__ = ["FriendsService"]
