import os
import uuid
from typing import Annotated, AsyncGenerator, Optional

from fastapi import Depends, WebSocket
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from backend.core.user import User
from backend.db import *
from backend.repositories.orm.user_orm import UserORM

cookie_transport = CookieTransport(cookie_name="auth", cookie_max_age=3600)

SECRET = os.getenv("AUTH_SECRET", "rEpEeWsEnIm")

WS_UNAUTHORIZED = 4001
WS_INVALID_TOKEN = 4002
WS_USER_NOT_FOUND = 4003


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(UUIDIDMixin, BaseUserManager[UserORM, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, UserORM)


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[UserORM, uuid.UUID](get_user_manager, [auth_backend])


def get_current_user(
    orm_user: UserORM = Depends(fastapi_users.current_user(active=True)),
) -> User:
    return orm_user.to_user()


def get_optional_current_user(
    orm_user: Optional[UserORM] = Depends(
        fastapi_users.current_user(active=True, optional=True)
    )
) -> Optional[User]:
    if orm_user is None:
        return None
    return orm_user.to_user()


CurrentUser = Annotated[UserORM, Depends(get_current_user)]
OptionalCurrentUser = Annotated[Optional[UserORM], Depends(get_optional_current_user)]


async def get_user_from_websocket(
    websocket: WebSocket,
    user_manager: UserManager = Depends(get_user_manager),
) -> User:
    from fastapi import WebSocketException

    token = websocket.cookies.get("auth")

    if not token:
        raise WebSocketException(code=WS_UNAUTHORIZED, reason="Missing auth token")

    try:
        strategy = get_jwt_strategy()
        user = await strategy.read_token(token, user_manager)

        if not user or not user.is_active:
            raise WebSocketException(code=WS_USER_NOT_FOUND, reason="User not found")

        return user.to_user()

    except WebSocketException:
        raise
    except Exception as e:
        raise WebSocketException(
            code=WS_INVALID_TOKEN, reason="Invalid or expired token"
        ) from e


CurrentUserWebSocket = Annotated[User, Depends(get_user_from_websocket)]
