import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

import backend.services.exceptions as service_exceptions
from backend import services
from backend.lib.auth import CurrentUser
from backend.routers.websockets.connections_manager import connections_manager

from .schemas.user_schemas import *

PaginationParams = Annotated[Params, Depends()]
FriendsService = Annotated[services.FriendsService, Depends()]

friends_exceptions = {
    service_exceptions.UsersNotFriends: HTTPException(400, "Users are not friends"),
    service_exceptions.FriendRequestNotExists: HTTPException(
        404, "Friend request not found"
    ),
    service_exceptions.UsersAlreadyFriends: HTTPException(
        400, "Users are already friends"
    ),
    service_exceptions.FriendRequestAlreadySent: HTTPException(
        400, "Friend request already exists"
    ),
    service_exceptions.CannotFriendRequestYourself: HTTPException(
        400, "Cannot send friend request to oneself"
    ),
    service_exceptions.RequestedFriendNotExists: HTTPException(
        404, "Requested friend not found"
    ),
}

friends_router = APIRouter(prefix="/friends", tags=["friends"])
friend_requests_router = APIRouter(prefix="/friend-requests", tags=["friend-requests"])


async def notify(receiver_id: uuid.UUID, data: FriendRequest):
    if connections_manager.is_user_online(receiver_id):
        websocket = connections_manager.get(receiver_id)
        await websocket.send_text(
            FriendRequestNotificationResponse.from_friend_request(
                data
            ).model_dump_json()
        )


@friends_router.get(
    "",
    responses={200: {"model": Page[FriendResponse]}},
)
async def get_friends(
    user: CurrentUser,
    service: FriendsService,
    pagination_params: PaginationParams,
):
    """Gets a list of friends for current user"""
    page = await service.get_friends(pagination_params)
    page.items = [FriendResponse.from_user(friend) for friend in page.items]
    return page


@friends_router.delete("/{friend_id}")
async def remove_friend(
    friend_id: uuid.UUID,
    user: CurrentUser,
    service: FriendsService,
):
    """Removes a friend from friends list"""
    return await service.remove_friend(friend_id)


@friend_requests_router.get(
    "/pending",
    responses={200: {"model": Page[FriendRequestResponse]}},
)
async def get_pending_friend_requests(
    user: CurrentUser,
    service: FriendsService,
    pagination_params: PaginationParams,
):
    """Lists pending friend requests for current user"""
    page = await service.get_pending_friend_requests(pagination_params)
    page.items = [FriendRequestResponse.from_friend_request(req) for req in page.items]
    return page


@friend_requests_router.get(
    "/sent",
    responses={200: {"model": Page[FriendRequestResponse]}},
)
async def get_sent_friend_requests(
    user: CurrentUser,
    service: FriendsService,
    pagination_params: PaginationParams,
):
    """Lists sent friend requests for current user"""
    page = await service.get_sent_friend_requests(pagination_params)
    page.items = [FriendRequestResponse.from_friend_request(req) for req in page.items]
    return page


@friend_requests_router.post("")
async def make_friend_request(
    body: MakeFriendRequest,
    user: CurrentUser,
    service: FriendsService,
):
    """Makes a friend request to user with given id"""
    friend_request = await service.make_friend_request(body.friend_id, notify)
    return FriendRequestResponse.from_friend_request(friend_request)


@friend_requests_router.post("/{friend_request_id}/accept")
async def accept_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: FriendsService,
):
    """Accepts friend request with given id"""
    await service.accept_friend_request(friend_request_id)


@friend_requests_router.post("/{friend_request_id}/reject")
async def reject_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: FriendsService,
):
    """Rejects friend request with given id"""
    await service.reject_friend_request(friend_request_id)
