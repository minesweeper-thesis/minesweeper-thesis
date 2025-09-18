import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, Params

from backend import schemas, services
from backend.services.auth_service import CurrentUser

user_router = APIRouter()

PaginationParams = Annotated[Params, Depends()]
UserService = Annotated[services.UserService, Depends()]


@user_router.post("/gameplays", status_code=204)
async def save_gameplay(
    gameplay: schemas.Gameplay,
    user: CurrentUser,
    service: UserService,
):
    """Saves gameplay for current user"""
    await service.save_gameplay(
        user.id,
        gameplay.board_id,
        gameplay.score,
        gameplay.time,
        gameplay.used_prompts,
    )


@user_router.get("/gameplays")
async def get_gameplays(
    user: CurrentUser,
    service: UserService,
    pagination_params: PaginationParams,
) -> Page[schemas.Gameplay]:
    """Gets gameplays for current user"""
    return await service.get_gameplays(user.id, pagination_params)


@user_router.get("/friends")
async def get_friends(
    user: CurrentUser,
    service: UserService,
    pagination_params: PaginationParams,
) -> Page[schemas.Friend]:
    """Gets a list of friends for current user"""
    return await service.get_friends(user.id, pagination_params)


@user_router.put("/friends/{friend_id}")
async def make_friend_request(
    friend_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Makes a friend request to user with given id"""
    return await service.make_friend_request(user.id, friend_id)


@user_router.get("/friends/pending", response_model=Page[schemas.FriendRequest])
async def get_pending_friend_requests(
    user: CurrentUser,
    service: UserService,
    pagination_params: PaginationParams,
):
    """Lists pending friend requests for current user"""
    return await service.get_pending_friend_requests(user.id, pagination_params)


@user_router.post("/friends/accept/{friend_request_id}")
async def accept_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Accepts friend request with given id"""
    return await service.accept_friend_request(user.id, friend_request_id)


@user_router.post("/friends/reject/{friend_request_id}")
async def reject_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Rejects friend request with given id"""
    return await service.reject_friend_request(user.id, friend_request_id)


@user_router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Removes a friend from friends list"""
    return await service.remove_friend(user.id, friend_id)
