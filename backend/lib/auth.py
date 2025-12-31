import logging
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

from backend.config import AUTH_SECRET
from backend.core.user import User
from backend.db import *
from backend.lib.online_users import OnlineUsersStore, get_online_users_store
from backend.repositories.orm.user_orm import UserORM

logger = logging.getLogger(__name__)

cookie_transport = CookieTransport(cookie_name="auth", cookie_max_age=3600)


WS_UNAUTHORIZED = 4001
WS_INVALID_TOKEN = 4002
WS_USER_NOT_FOUND = 4003


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=str(AUTH_SECRET), lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(UUIDIDMixin, BaseUserManager[UserORM, uuid.UUID]):
    reset_password_token_secret = str(AUTH_SECRET)
    verification_token_secret = str(AUTH_SECRET)


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, UserORM)


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[UserORM, uuid.UUID](get_user_manager, [auth_backend])


async def get_current_user(
    user_orm: Annotated[UserORM, Depends(fastapi_users.current_user(active=True))],
    online_users_store: Annotated[OnlineUsersStore, Depends(get_online_users_store)],
) -> User:
    is_online = await online_users_store.is_user_online(user_orm.id)
    logger.debug(f"User {user_orm.id} authenticated, is_online={is_online}")
    return user_orm.to_user(is_online=is_online)


async def get_optional_current_user(
    user_orm: Annotated[
        Optional[UserORM],
        Depends(fastapi_users.current_user(active=True, optional=True)),
    ],
    online_users_store: Annotated[OnlineUsersStore, Depends(get_online_users_store)],
) -> Optional[User]:
    if user_orm is None:
        return None
    is_online = await online_users_store.is_user_online(user_orm.id)
    return user_orm.to_user(is_online=is_online)


CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalCurrentUser = Annotated[Optional[User], Depends(get_optional_current_user)]


async def get_user_from_websocket(
    websocket: WebSocket,
    user_manager: UserManager = Depends(get_user_manager),
) -> User:
    from fastapi import WebSocketException

    token = websocket.cookies.get("auth")

    if not token:
        logger.warning("WebSocket connection attempt without auth token")
        raise WebSocketException(code=WS_UNAUTHORIZED, reason="Missing auth token")

    try:
        strategy = get_jwt_strategy()
        user = await strategy.read_token(token, user_manager)

        if not user or not user.is_active:
            logger.warning(f"WebSocket auth failed: user not found or inactive")
            raise WebSocketException(code=WS_USER_NOT_FOUND, reason="User not found")

        logger.debug(f"User {user.id} authenticated via WebSocket")
        return user.to_user(is_online=True)

    except WebSocketException:
        raise
    except Exception as e:
        logger.error(f"WebSocket auth error: {e}")
        raise WebSocketException(
            code=WS_INVALID_TOKEN, reason="Invalid or expired token"
        ) from e


CurrentUserWebSocket = Annotated[User, Depends(get_user_from_websocket)]
