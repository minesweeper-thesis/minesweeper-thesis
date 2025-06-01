from typing import AsyncGenerator, AsyncIterator

from fastapi import Depends, FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    CookieTransport,
    JWTStrategy,
)
from fastapi_users.schemas import BaseUser, BaseUserCreate

from algorithms.boards.random_board import RandomBoard

from .db import *
from .models import *


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield
    await engine.dispose()


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


app = FastAPI()

# Konfiguracja CORS niezbyt specyficzna, ale chciałem coś co działa bez zabawy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/board")
async def get_board(rows: int, cols: int, start_x: int, start_y: int, mine_count: int):
    print(rows, cols, (start_x, start_y), mine_count)
    board = RandomBoard(rows, cols, (start_x, start_y), mine_count)
    board.grid().print_solved()
    return board.grid().grid


app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth",
    tags=["auth"],
)


class UserCreate(BaseUserCreate):
    nickname: str
    generator_settings: str


from uuid import UUID


class UserRead(BaseUser[UUID]):
    nickname: str

    class Config:
        from_attributes = True


class UserUpdate(BaseUserCreate):
    nickname: str


app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/auth",
    tags=["auth"],
)
