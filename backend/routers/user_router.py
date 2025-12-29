import uuid
from typing import Annotated, Optional

import filetype
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from fastapi_pagination import Page, Params

from backend import services
from backend.core.game import GameMode, GameResult, GameStatus
from backend.lib.auth import CurrentUser
from backend.schemas.user import *
from backend.services.exceptions import UserNotExists

PaginationParams = Annotated[Params, Depends()]
UserService = Annotated[services.UserService, Depends()]
UserChatService = Annotated[services.UserChatService, Depends()]

user_exceptions: dict[type[Exception], HTTPException] = {
    UserNotExists: HTTPException(status_code=404, detail="User not found."),
}

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

    url = await service.set_avatar(user, content)
    return {"avatar_url": url}


@user_router.delete("/avatar")
async def delete_avatar(
    user: CurrentUser,
    service: UserService,
):
    """Deletes the current user's avatar"""
    await service.delete_avatar(user)


@user_router.get(
    "/search",
    responses={200: {"model": Page[UserResponse]}},
)
async def search_users(
    user: CurrentUser,
    query: str,
    pagination_params: PaginationParams,
    service: UserService,
):
    page = await service.search_users(query, pagination_params)
    page.items = [UserResponse.build(user) for user in page.items]  # type: ignore[misc]
    return page


@user_router.get("/gameplays", responses={200: {"model": Page[UserGameplayResponse]}})
async def get_gameplays(
    user: CurrentUser,
    pagination_params: PaginationParams,
    service: UserService,
    status: Annotated[Optional[GameStatus], Query()] = None,
    result: Annotated[Optional[GameResult], Query()] = None,
    used_hints: Annotated[Optional[bool], Query()] = None,
    min_time: Annotated[Optional[float], Query()] = None,
    max_time: Annotated[Optional[float], Query()] = None,
    mode: Annotated[Optional[GameMode], Query()] = None,
):
    page = await service.get_gameplays(
        user,
        pagination_params,
        status=status,
        result=result,
        used_hints=used_hints,
        min_time=min_time,
        max_time=max_time,
        mode=mode,
    )
    page.items = [UserGameplayResponse.build(gp) for gp in page.items]  # type: ignore[misc]
    return page


@user_router.post("/chat-messages")
async def send_chat_message(
    user: CurrentUser,
    service: UserChatService,
    request: UserChatMessageRequest,
):
    """Sends a chat message in the lobby."""
    await service.send_chat_message(user, request.user_id, request.content)


@user_router.get(
    "/chat-messages", responses={200: {"model": Page[UserChatMessageResponse]}}
)
async def get_chat_messages(
    user: CurrentUser,
    user_id: uuid.UUID,
    service: UserChatService,
    pagination_params: PaginationParams,
):
    """Retrieves chat messages from the lobby."""
    page = await service.get_chat_messages(user, user_id, pagination_params)
    page.items = [UserChatMessageResponse.build(message) for message in page.items]  # type: ignore
    return page
