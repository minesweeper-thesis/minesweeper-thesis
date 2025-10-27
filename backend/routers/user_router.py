import uuid
from typing import Annotated

import filetype
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi_pagination import Page, Params

import backend.schemas.user_schemas as schemas
import backend.services.exceptions as service_exceptions
from backend import services
from backend.services.auth_service import CurrentUser

PaginationParams = Annotated[Params, Depends()]
UserService = Annotated[services.UserService, Depends()]

user_exceptions = {
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

user_router = APIRouter(tags=["user"])


@user_router.put("/avatar")
async def upload_avatar(file: UploadFile, user: CurrentUser, service: UserService):
    content = await file.read()
    kind = filetype.guess(content)
    if (
        kind is None
        or not kind.mime.startswith("image/")
        or file.content_type != kind.mime
    ):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    url = await service.set_avatar(content)
    return {"avatar_url": url}


@user_router.delete("/avatar")
async def delete_avatar(
    user: CurrentUser,
    service: UserService,
):
    """Deletes the current user's avatar"""
    await service.delete_avatar()


@user_router.get("/friends")
async def get_friends(
    user: CurrentUser,
    service: UserService,
    pagination_params: PaginationParams,
) -> Page[schemas.Friend]:
    """Gets a list of friends for current user"""
    return await service.get_friends(pagination_params)


@user_router.put("/friends/{friend_id}")
async def make_friend_request(
    friend_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Makes a friend request to user with given id"""
    return await service.make_friend_request(friend_id)


@user_router.get("/friends/pending", response_model=Page[schemas.FriendRequest])
async def get_pending_friend_requests(
    user: CurrentUser,
    service: UserService,
    pagination_params: PaginationParams,
):
    """Lists pending friend requests for current user"""
    return await service.get_pending_friend_requests(pagination_params)


@user_router.post("/friends/accept/{friend_request_id}")
async def accept_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Accepts friend request with given id"""
    return await service.accept_friend_request(friend_request_id)


@user_router.post("/friends/reject/{friend_request_id}")
async def reject_friend_request(
    friend_request_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Rejects friend request with given id"""
    return await service.reject_friend_request(friend_request_id)


@user_router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: uuid.UUID,
    user: CurrentUser,
    service: UserService,
):
    """Removes a friend from friends list"""
    return await service.remove_friend(friend_id)
