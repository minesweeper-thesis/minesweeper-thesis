import uuid
from typing import Optional

from fastapi_pagination import Params
from fastapi_pagination.ext.sqlalchemy import apaginate
from sqlalchemy import select
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm import selectinload

from backend.core.user import FriendRequest, FriendRequestStatus, Friendship
from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class FriendsRepository:
    def __init__(self, session: DBSession):
        self.session = session

    async def get_friends(self, user_id: uuid.UUID, pagination_params: Params):
        stmt = (
            select(UserORM)
            .join(UserORM.friend_of)
            .where(FriendshipORM.user_id == user_id)
        )
        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [user.to_user() for user in items],
        )

    async def get_friend_request(
        self,
        id: Optional[uuid.UUID] = None,
        user_id: Optional[uuid.UUID] = None,
        friend_id: Optional[uuid.UUID] = None,
        status: Optional[FriendRequestStatus] = None,
    ):
        args = []
        if id:
            args.append(FriendRequestORM.id == id)
        if user_id:
            args.append(FriendRequestORM.user_id == user_id)
        if friend_id:
            args.append(FriendRequestORM.friend_id == friend_id)
        if status:
            args.append(FriendRequestORM.status == status)

        try:
            stmt = (
                select(FriendRequestORM)
                .options(
                    selectinload(FriendRequestORM.user),
                    selectinload(FriendRequestORM.friend),
                )
                .where(*args)
            )
            result = await self.session.execute(stmt)
            return result.scalar_one().to_friend_request()

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
            args.append(FriendRequestORM.user_id == user_id)
        if friend_id:
            args.append(FriendRequestORM.friend_id == friend_id)
        if status:
            args.append(FriendRequestORM.status == status)

        stmt = (
            select(FriendRequestORM)
            .options(
                selectinload(FriendRequestORM.user),
                selectinload(FriendRequestORM.friend),
            )
            .where(*args)
        )
        return await apaginate(
            self.session,
            stmt,
            pagination_params,
            transformer=lambda items: [
                friend_request.to_friend_request() for friend_request in items
            ],
        )

    async def add_friendship(self, friendship: Friendship):
        self.session.add(FriendshipORM.from_friendship(friendship))
        await self.session.commit()

    async def add_friend_request(self, friend_request: FriendRequest):
        friend_request_orm = FriendRequestORM.from_friend_request(friend_request)
        self.session.add(friend_request_orm)
        await self.session.commit()

    async def change_friend_request_status(
        self, friend_request_id: uuid.UUID, status: FriendRequestStatus
    ):
        try:
            stmt = select(FriendRequestORM).where(
                FriendRequestORM.id == friend_request_id,
            )
            result = await self.session.execute(stmt)
            friend_request = result.scalar_one()

            friend_request.status = status
            await self.session.commit()

        except NoResultFound:
            raise FriendRequestNotFound() from None

    async def get_friendship(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        try:
            stmt = select(FriendshipORM).where(
                FriendshipORM.user_id == user_id,
                FriendshipORM.friend_id == friend_id,
            )
            result = await self.session.execute(stmt)
            return result.scalar_one().to_friendship()

        except NoResultFound:
            raise FriendshipNotFound() from None

    async def remove_friendship(self, user_id: uuid.UUID, friend_id: uuid.UUID):
        try:
            stmt = select(FriendshipORM).where(
                FriendshipORM.user_id == user_id, FriendshipORM.friend_id == friend_id
            )
            result = await self.session.execute(stmt)
            friendship = result.scalar_one()
            await self.session.delete(friendship)
            await self.session.commit()

        except NoResultFound:
            raise FriendshipNotFound() from None
