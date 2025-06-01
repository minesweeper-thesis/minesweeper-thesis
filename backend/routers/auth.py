from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)

from ..db import *
from ..models import *
from ..schemas import *

auth_router = APIRouter()


cookie_transport = CookieTransport(cookie_name="auth", cookie_max_age=3600)

SECRET = "rEpEeWsEnIm"


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    user_db_model = User
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET


async def get_user_manager(
    user_db=Depends(get_user_db),
) -> AsyncGenerator[UserManager, None]:
    yield UserManager(user_db)


fastapi_users = FastAPIUsers[User, int](get_user_manager, [auth_backend])


auth_router.include_router(fastapi_users.get_auth_router(auth_backend))

auth_router.include_router(fastapi_users.get_register_router(UserRead, UserCreate))

auth_router.include_router(fastapi_users.get_users_router(UserRead, UserUpdate))
