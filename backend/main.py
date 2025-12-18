import logging
import os
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi_pagination import add_pagination

from backend import routers
from backend.config import FRONTEND_URL
from backend.lib.lobby_offline_users_kicker import (
    initialize_lobby_kicker,
    shutdown_lobby_kicker,
)
from backend.lib.redis_client import initialize_redis, shutdown_redis
from backend.lib.scheduler import initialize_scheduler, shutdown_scheduler

from .db import *

handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

backend_logger = logging.getLogger("backend")
backend_logger.setLevel(logging.DEBUG)
backend_logger.addHandler(handler)
backend_logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    initialize_scheduler()
    await init_db()
    await initialize_redis()
    await initialize_lobby_kicker()

    yield

    shutdown_scheduler()
    await shutdown_lobby_kicker()
    await shutdown_redis()
    await engine.dispose()


api = FastAPI()

routers.register_exceptions(api)

api.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(routers.auth_router, prefix="/auth")
api.include_router(routers.game_router, prefix="/game")
api.include_router(routers.lobby_router)
api.include_router(routers.invitations_router)
api.include_router(routers.stats_router)
api.include_router(routers.user_router)
api.include_router(routers.friends_router)
api.include_router(routers.friend_requests_router)
api.include_router(routers.notifications_router)
add_pagination(api)

os.makedirs("img", exist_ok=True)
api.mount(
    "/img",
    StaticFiles(directory="img"),
    name="img",
)


app = FastAPI(lifespan=lifespan)
app.mount("/api", api)

frontend_build_path = Path(__file__).parent.parent / "frontend" / "dist"

if frontend_build_path.exists():

    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        index_path = frontend_build_path / "index.html"
        file_path = frontend_build_path / full_path
        file_path = file_path.resolve()

        if not file_path.is_relative_to(frontend_build_path):
            return FileResponse(index_path)

        if file_path.is_file():
            return FileResponse(file_path)

        return FileResponse(index_path)
