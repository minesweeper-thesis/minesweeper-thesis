from typing import Annotated

import filetype
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi_pagination import Page, Params

from backend import services
from backend.lib.auth import CurrentUser

from .schemas.user_schemas import *

PaginationParams = Annotated[Params, Depends()]
UserService = Annotated[services.UserService, Depends()]

user_exceptions = {}

user_router = APIRouter(tags=["user"])


@user_router.post("/avatar")
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


@user_router.get(
    "/search",
    responses={200: {"model": Page[UserResponse]}},
)
async def search_users(
    query: str,
    pagination_params: PaginationParams,
    service: UserService,
):
    page = await service.search_users(query, pagination_params)
    page.items = [UserResponse.from_user(user) for user in page.items]
    return page


@user_router.get("/gameplays", responses={200: {"model": Page[UserGameplayResponse]}})
async def get_gameplays(
    pagination_params: PaginationParams,
    service: UserService,
):
    page = await service.get_gameplays(pagination_params)
    page.items = [UserGameplayResponse.from_gameplay(gp) for gp in page.items]
    return page
