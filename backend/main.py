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

os.makedirs("img", exist_ok=True)
api.mount(
    "/img",
    StaticFiles(directory="img"),
    name="img",
)

routers.register_exceptions(api)

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


app = FastAPI()
app.mount("/api", api)

frontend_build_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "frontend", "build"
)
if os.path.exists(frontend_build_path):
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(frontend_build_path, "static")),
        name="static",
    )
    app.mount(
        "/", StaticFiles(directory=frontend_build_path, html=True), name="frontend"
    )
