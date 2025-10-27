import os
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from backend import routers

from .db import *


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.mount(
    "/static",
    StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../static")),
    name="static",
)

routers.register_exceptions(app)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routers.auth_router, prefix="/auth")
app.include_router(routers.game_router)
app.include_router(routers.stats_router)
app.include_router(routers.user_router)
add_pagination(app)
