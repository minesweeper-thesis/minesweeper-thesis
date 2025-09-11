import uuid

from fastapi import APIRouter, Depends
from fastapi_pagination import Page, Params

from backend import schemas
from backend.models import User
from backend.services import auth_service, user_service

user_router = APIRouter()

current_user: User = Depends(auth_service.get_current_user)


@user_router.post("/gameplays", status_code=204)
async def save_gameplay(gameplay: schemas.Gameplay, user=current_user):
    """Saves gameplay for current user"""
    await user_service.save_gameplay(
        user.id, gameplay.board_id, gameplay.score, gameplay.time, gameplay.used_prompts
    )


@user_router.get("/gameplays")
async def get_gameplays(
    user=current_user, pagination_params: Params = Depends()
) -> Page[schemas.Gameplay]:
    """Gets gameplays for current user"""
    return await user_service.get_gameplays(user.id, pagination_params)


@user_router.get("/friends")
async def get_friends(
    user=current_user, pagination_params: Params = Depends()
) -> Page[schemas.Friend]:
    """Gets a list of friends for current user"""
    return await user_service.get_friends(user.id, pagination_params)


@user_router.put("/friends/{friend_id}")
async def make_friend_request(friend_id: uuid.UUID, user=current_user):
    """Makes a friend request to user with given id"""
    return await user_service.make_friend_request(user.id, friend_id)


@user_router.get("/friends/pending", response_model=Page[schemas.FriendRequest])
async def get_pending_friend_requests(
    user=current_user,
    pagination_params: Params = Depends(),
):
    """Lists pending friend requests for current user"""
    return await user_service.get_pending_friend_requests(user.id, pagination_params)


@user_router.post("/friends/accept/{friend_request_id}")
async def accept_friend_request(friend_request_id: uuid.UUID, user=current_user):
    """Accepts friend request with given id"""
    return await user_service.accept_friend_request(user.id, friend_request_id)


@user_router.post("/friends/reject/{friend_request_id}")
async def reject_friend_request(friend_request_id: uuid.UUID, user=current_user):
    """Rejects friend request with given id"""
    return await user_service.reject_friend_request(user.id, friend_request_id)


@user_router.delete("/friends/{friend_id}")
async def remove_friend(friend_id: uuid.UUID, user=current_user):
    """Removes a friend from friends list"""
    return await user_service.remove_friend(user.id, friend_id)
