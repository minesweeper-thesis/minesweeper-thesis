import uuid

from fastapi_pagination import Params

from backend.db import *
from backend.models import *
from backend.repositories import user_repo


async def save_gameplay(
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
    await user_repo.add_gameplay(gameplay)


async def get_gameplays(user_id: uuid.UUID, pagination_params: Params):
    return await user_repo.get_gameplays(user_id, pagination_params)


async def get_friends(user_id: uuid.UUID, pagination_params: Params):
    return await user_repo.get_friends(user_id, pagination_params)


async def get_pending_friend_requests(user_id: uuid.UUID, pagination_params: Params):
    return await user_repo.get_friend_requests(
        friend_id=user_id,
        status=FriendRequestStatus.pending,
        pagination_params=pagination_params,
    )


async def make_friend_request(user_id: uuid.UUID, friend_id: uuid.UUID):
    if user_id == friend_id:
        return

    friend_request = await user_repo.get_friend_requests(
        user_id=user_id, friend_id=friend_id, status=FriendRequestStatus.pending
    )
    if friend_request:
        return

    friend_request = FriendRequest(
        user_id=user_id, friend_id=friend_id, status=FriendRequestStatus.pending
    )
    return await user_repo.add_friend_request(friend_request)


async def accept_friend_request(user_id: uuid.UUID, friend_request_id: uuid.UUID):
    friend_requests = await user_repo.get_friend_requests(
        id=friend_request_id, friend_id=user_id, status=FriendRequestStatus.pending
    )
    if not len(friend_requests):
        return
    friend_request = friend_requests[0]

    await user_repo.add_friendship(
        Friendship(user_id=friend_request.user_id, friend_id=friend_request.friend_id)
    )
    await user_repo.add_friendship(
        Friendship(user_id=friend_request.friend_id, friend_id=friend_request.user_id)
    )
    await user_repo.change_friend_request_status(
        friend_request_id, FriendRequestStatus.accepted
    )


async def reject_friend_request(user_id: uuid.UUID, friend_request_id: uuid.UUID):
    friend_requests = await user_repo.get_friend_requests(
        id=friend_request_id, friend_id=user_id, status=FriendRequestStatus.pending
    )
    if not len(friend_requests):
        return

    await user_repo.change_friend_request_status(
        friend_request_id, FriendRequestStatus.rejected
    )


async def remove_friend(user_id: uuid.UUID, friend_id: uuid.UUID):
    friendship1 = await user_repo.get_friendship(user_id, friend_id)
    friendship2 = await user_repo.get_friendship(friend_id, user_id)

    if friendship1:
        await user_repo.remove_friendship(friendship1)
    if friendship2:
        await user_repo.remove_friendship(friendship2)
