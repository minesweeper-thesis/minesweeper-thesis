import uuid
from typing import Annotated, Optional

from fastapi import Depends
from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_async_session
from ..models import FriendRequest, FriendRequestStatus, Friendship, Gameplay, User


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

    async def get_friend_requests(
        self,
        id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        friend_id: Optional[uuid.UUID] = None,
        status: Optional[FriendRequestStatus] = None,
        pagination_params: Params | None = None,
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

        stmt = select(FriendRequest).where(*args)
        if pagination_params:
            return await apaginate(self.session, stmt, pagination_params)
        result = await self.session.execute(stmt)
        return result.scalars().all()

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
        stmt = select(FriendRequest).where(
            FriendRequest.id == friend_request_id,
        )
        result = await self.session.execute(stmt)
        friend_request = result.scalar()

        if not friend_request:
            raise ValueError("Friend request not found")

        friend_request.status = status  # type: ignore
        await self.session.commit()
        await self.session.refresh(friend_request)

    async def get_friendship(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        stmt = select(Friendship).where(
            Friendship.user_id == user_id,
            Friendship.friend_id == friend_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar()

    async def remove_friendship(self, friendship_id: uuid.UUID):
        stmt = select(Friendship).where(Friendship.id == friendship_id)
        result = await self.session.execute(stmt)
        friendship = result.scalar()
        if friendship:
            await self.session.delete(friendship)
            await self.session.commit()
