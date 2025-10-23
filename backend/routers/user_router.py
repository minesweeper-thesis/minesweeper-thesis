import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from fastapi.concurrency import asynccontextmanager
from fastapi_pagination import Page, Params

import backend.services.exceptions as service_exceptions
from backend import schemas, services
from backend.services.auth_service import CurrentUser

PaginationParams = Annotated[Params, Depends()]
UserService = Annotated[services.UserService, Depends()]

exceptions = {
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
}


def register_exceptions(app: FastAPI):
    for service_exception, router_exception in exceptions.items():

        async def handler(request, exception, router_exception=router_exception):
            raise router_exception

        app.add_exception_handler(service_exception, handler)


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_exceptions(app)
    yield


user_router = APIRouter(lifespan=lifespan, tags=["user"])


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
        gameplay.time,
        gameplay.used_prompts,
        gameplay.won,
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
