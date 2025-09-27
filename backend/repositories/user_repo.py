import uuid
from typing import Annotated, Optional

from fastapi import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import FriendRequest, FriendRequestStatus, Friendship, Gameplay, User
from .exceptions import *


class UserRepository:
    def __init__(self, session: Annotated[AsyncSession, Depends(get_async_session)]):
        self.session = session

    async def add_gameplay(self, gameplay: Gameplay):
        self.session.add(gameplay)
        await self.session.commit()
        await self.session.refresh(gameplay)
        return gameplay

    async def get_gameplays(self, user_id: uuid.UUID, pagination_params: Params):
        stmt = select(Gameplay).where(Gameplay.user_id == user_id)
        return await apaginate(self.session, stmt, pagination_params)

    async def get_friends(self, user_id: uuid.UUID, pagination_params: Params):
        stmt = select(User).join(User.friend_of).where(Friendship.user_id == user_id)
        return await apaginate(self.session, stmt, pagination_params)

    async def get_friend_request(
        self,
        id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        friend_id: Optional[uuid.UUID] = None,
        status: Optional[FriendRequestStatus] = None,
    ):
        args = []
        if id:
            args.append(FriendRequest.id == id)
        if user_id:
            args.append(FriendRequest.user_id == user_id)
        if friend_id:
            args.append(FriendRequest.friend_id == friend_id)
        if status:
            args.append(FriendRequest.status == status)

        try:
            stmt = select(FriendRequest).where(*args)
            result = await self.session.execute(stmt)
            return result.scalar_one()

        except NoResultFound:
            raise FriendRequestNotFound() from None

    async def get_friend_requests(
        self,
        pagination_params: Params,
        user_id: Optional[uuid.UUID] = None,
        friend_id: Optional[uuid.UUID] = None,
        status: Optional[FriendRequestStatus] = None,
    ):
        args = []
        if user_id:
            args.append(FriendRequest.user_id == user_id)
        if friend_id:
            args.append(FriendRequest.friend_id == friend_id)
        if status:
            args.append(FriendRequest.status == status)

        stmt = select(FriendRequest).where(*args)
        return await apaginate(self.session, stmt, pagination_params)

    async def add_friendship(self, friendship: Friendship):
        self.session.add(friendship)
        await self.session.commit()
        await self.session.refresh(friendship)
        return friendship

    async def add_friend_request(self, friend_request: FriendRequest):
        self.session.add(friend_request)
        await self.session.commit()
        await self.session.refresh(friend_request)
        return friend_request

    async def change_friend_request_status(
        self, friend_request_id: uuid.UUID, status: FriendRequestStatus
    ):
        try:
            stmt = select(FriendRequest).where(
                FriendRequest.id == friend_request_id,
            )
            result = await self.session.execute(stmt)
            friend_request = result.scalar_one()

            friend_request.status = status
            await self.session.commit()
            await self.session.refresh(friend_request)

        except NoResultFound:
            raise FriendRequestNotFound() from None

    async def get_friendship(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        try:
            stmt = select(Friendship).where(
                Friendship.user_id == user_id,
                Friendship.friend_id == friend_id,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one()

        except NoResultFound:
            raise FriendshipNotFound() from None

    async def remove_friendship(self, friendship_id: uuid.UUID):
        try:
            stmt = select(Friendship).where(Friendship.id == friendship_id)
            result = await self.session.execute(stmt)
            friendship = result.scalar_one()
            await self.session.delete(friendship)
            await self.session.commit()

        except NoResultFound:
            raise FriendshipNotFound() from None
