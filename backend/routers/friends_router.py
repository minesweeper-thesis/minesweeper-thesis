import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi_pagination import Page, Params

from backend import services
from backend.lib.auth import CurrentUser
from backend.services import exceptions

from .schemas.user import *

PaginationParams = Annotated[Params, Depends()]
FriendsService = Annotated[services.FriendsService, Depends()]

friends_exceptions = {
    exceptions.UsersNotFriends: HTTPException(400, "Users are not friends"),
    exceptions.FriendRequestNotExists: HTTPException(404, "Friend request not found"),
    exceptions.UsersAlreadyFriends: HTTPException(400, "Users are already friends"),
    exceptions.FriendRequestAlreadySent: HTTPException(
        400, "Friend request already exists"
    ),
    exceptions.CannotFriendRequestYourself: HTTPException(
        400, "Cannot send friend request to oneself"
    ),
    exceptions.RequestedFriendNotExists: HTTPException(
        404, "Requested friend not found"
    ),
}

friends_router = APIRouter(prefix="/friends", tags=["friends"])
friend_requests_router = APIRouter(prefix="/friend-requests", tags=["friend-requests"])


@friends_router.get(
    "",
    responses={200: {"model": Page[UserResponse]}},
)
async def get_friends(
    user: CurrentUser,
    service: FriendsService,
    pagination_params: PaginationParams,
):
    """Gets a list of friends for current user"""
    page = await service.get_friends(user, pagination_params)
    page.items = [UserResponse.build(friend) for friend in page.items]
    return page


@friends_router.delete("/{friend_id}")
async def remove_friend(
    friend_id: uuid.UUID,
    user: CurrentUser,
    service: FriendsService,
):
    """Removes a friend from friends list"""
    return await service.remove_friend(user, friend_id)


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
    page = await service.get_pending_friend_requests(user, pagination_params)
    page.items = [FriendRequestResponse.build(req) for req in page.items]
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
    page = await service.get_sent_friend_requests(user, pagination_params)
    page.items = [FriendRequestResponse.build(req) for req in page.items]
    return page


@friend_requests_router.post("")
async def make_friend_request(
    body: MakeFriendRequest,
    user: CurrentUser,
    service: FriendsService,
):
    """Makes a friend request to user with given id"""
    friend_request = await service.make_friend_request(user, body.friend_id)
    return FriendRequestResponse.build(friend_request)


@friend_requests_router.post("/{friend_request_id}/accept")
async def accept_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: FriendsService,
):
    """Accepts friend request with given id"""
    await service.accept_friend_request(user, friend_request_id)


@friend_requests_router.post("/{friend_request_id}/reject")
async def reject_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: FriendsService,
):
    """Rejects friend request with given id"""
    await service.reject_friend_request(user, friend_request_id)
