import uuid
from typing import Optional

from sqlalchemy import select

from ..db import *
from ..models import *


async def add_gameplay(gameplay: Gameplay):
    async with async_session_maker() as db:
        db.add(gameplay)
        await db.commit()
        await db.refresh(gameplay)
        return gameplay


async def get_gameplays(user_id: uuid.UUID):
    async with async_session_maker() as db:
        stmt = select(Gameplay).where(Gameplay.user_id == user_id)
        result = await db.execute(stmt)
        return result.scalars().all()


async def get_friends(user_id: uuid.UUID):
    async with async_session_maker() as db:
        stmt = select(User).join(User.friend_of).where(Friendship.user_id == user_id)
        result = await db.execute(stmt)
        friends = result.scalars().all()
        return friends


async def get_friend_requests(
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

    async with async_session_maker() as db:
        stmt = select(FriendRequest).where(*args)
        result = await db.execute(stmt)
        return result.scalars().all()


async def add_friendship(friendship: Friendship):
    async with async_session_maker() as db:
        db.add(friendship)
        await db.commit()
        await db.refresh(friendship)
        return friendship


async def add_friend_request(friend_request: FriendRequest):
    async with async_session_maker() as db:
        db.add(friend_request)
        await db.commit()
        await db.refresh(friend_request)
        return friend_request


async def change_friend_request_status(
    friend_request_id: uuid.UUID, status: FriendRequestStatus
):
    async with async_session_maker() as db:
        stmt = select(FriendRequest).where(
            FriendRequest.id == friend_request_id,
        )
        result = await db.execute(stmt)
        friend_request = result.scalar()
        if not friend_request:
            return
        friend_request.status = status  # type: ignore
        await db.commit()
        await db.refresh(friend_request)


async def get_friendship(user_id: uuid.UUID, friend_id: uuid.UUID):
    async with async_session_maker() as db:
        stmt = select(Friendship).where(
            Friendship.user_id == user_id,
            Friendship.friend_id == friend_id,
        )
        result = await db.execute(stmt)
        return result.scalar()


async def remove_friendship(friendship_id: uuid.UUID):
    async with async_session_maker() as db:
        stmt = select(Friendship).where(Friendship.id == friendship_id)
        result = await db.execute(stmt)
        friendship = result.scalar()
        if friendship:
            await db.delete(friendship)
            await db.commit()
