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


api = FastAPI(lifespan=lifespan)

routers.register_exceptions(api)

routers.register_exceptions(app)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

api.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api.include_router(routers.auth_router, prefix="/auth")
api.include_router(routers.game_router)
api.include_router(routers.stats_router)
api.include_router(routers.user_router)
add_pagination(api)

os.makedirs("img", exist_ok=True)
api.mount(
    "/img",
    StaticFiles(directory="img"),
    name="img",
)


app = FastAPI()
app.mount("/api", api)

frontend_build_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "dist"
)
if os.path.exists(frontend_build_path):
    app.mount(
        "/", StaticFiles(directory=frontend_build_path, html=True), name="frontend"
    )
