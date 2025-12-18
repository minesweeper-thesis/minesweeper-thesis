import os
import random
import time
import uuid

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.core.board import Board

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"
os.environ["AUTH_SECRET"] = "test-secret-key"

from backend.db import db, get_async_session
from backend.main import api, app
from backend.repositories.orm import Base

db.engine = create_async_engine(
    os.environ["DATABASE_URL"],
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
db.async_session_maker = async_sessionmaker(db.engine, expire_on_commit=False)

engine = db.engine


class AuthenticatedClientBundle:
    def __init__(
        self,
        http_client: AsyncClient,
        ws_client: TestClient,
        user_data: dict,
        auth_cookie: str = "",
    ):
        self.http = http_client
        self.ws_client = ws_client
        self.user_data = user_data
        self.auth_cookie = auth_cookie or http_client.cookies.get("auth")
        self.user_id = None

    async def set_user_id(self):
        if not self.user_id:
            resp = await self.http.get("/api/auth/me")
            if resp.status_code == 200:
                self.user_id = resp.json().get("id")
        return self.user_id

    def get_ws(self):
        return self.ws_client.websocket_connect(
            "/api/ws", headers={"Cookie": f"auth={self.auth_cookie}"}
        )

    def get_ws_game(self, game_id: str):
        return self.ws_client.websocket_connect(
            f"/api/game/single/{game_id}",
            headers={"Cookie": f"auth={self.auth_cookie}"},
        )

    def get_ws_multi_game(self, session_id: str):
        return self.ws_client.websocket_connect(
            f"/api/game/multi/{session_id}",
            headers={"Cookie": f"auth={self.auth_cookie}"},
        )

    def get_ws_client(self):
        return self.ws_client

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return await self.http.__aexit__(*args)

    def __getattr__(self, name):
        return getattr(self.http, name)


@pytest.fixture(autouse=True)
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield


@pytest.fixture
async def session():
    async with db.async_session_maker() as session:
        yield session


@pytest.fixture(autouse=True)
async def override_dependency(session):
    from backend.lib.redis_client import get_redis

    async for redis_client in get_redis():
        await redis_client.flushdb()

    async def _override_db():
        yield session

    async def _override_redis():
        async for redis_client in get_redis():
            yield redis_client

    app.dependency_overrides[get_async_session] = _override_db
    app.dependency_overrides[get_redis] = _override_redis
    yield
    app.dependency_overrides = {}

    async for redis_client in get_redis():
        await redis_client.flushdb()


@pytest.fixture
async def client_no_auth(test_db, override_dependency):
    async with AsyncClient(
        transport=ASGITransport(app), base_url="https://testserver"
    ) as ac:
        yield ac


@pytest.fixture
def ws_client_no_auth(test_db, override_dependency):
    from fastapi.testclient import TestClient

    with TestClient(app, base_url="https://testserver") as c:
        yield c


@pytest.fixture
async def authenticated_clients(request, test_db, override_dependency):
    import uuid

    if hasattr(request, "param"):
        users_data = request.param
    else:
        uid = uuid.uuid4().hex[:8]
        users_data = [
            {
                "email": f"test-{uid}@example.com",
                "password": "pw",
                "nickname": f"test_{uid}",
            }
        ]

    with TestClient(app, base_url="https://testserver") as shared_ws_client:
        bundles = []
        for user_data in users_data:
            async_client = AsyncClient(
                transport=ASGITransport(app), base_url="https://testserver"
            )

            reg_resp = await async_client.post(
                "/api/auth/register",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "nickname": user_data["nickname"],
                    "settings": {},
                },
            )
            assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"

            login_resp = await async_client.post(
                "/api/auth/login",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            assert login_resp.status_code == 204, f"Login failed: {login_resp.text}"

            auth_cookie = login_resp.cookies.get("auth")
            assert auth_cookie, "Login did not set 'auth' cookie"

            domain = "testserver.local"
            async_client.cookies.set("auth", auth_cookie, domain=domain, path="/")

            bundle = AuthenticatedClientBundle(
                async_client, shared_ws_client, user_data, auth_cookie
            )
            await bundle.set_user_id()
            bundles.append(bundle)

        yield bundles

        for bundle in bundles:
            await bundle.http.aclose()

        await engine.dispose()
        time.sleep(0.01)


@pytest.fixture(autouse=True)
def board_generator_override():
    from backend.lib.board_generator import LocalBoardGenerator

    class ImmediateBoardGenerator:
        def __init__(self):
            self._statuses = {}

        async def generate_board(self, settings, on_completed):
            generation_id = uuid.uuid4()
            self._statuses[generation_id] = "completed"

            rows = settings.difficulty_level.rows
            cols = settings.difficulty_level.columns
            mines = settings.difficulty_level.mine_count

            start_field = (0, 0)
            cells = [
                (i, j)
                for i in range(rows)
                for j in range(cols)
                if (i, j) != start_field
            ]
            rng = random.Random(int.from_bytes(generation_id.bytes, "big"))
            minefields = rng.sample(cells, k=mines)

            board = Board(
                id=uuid.uuid4(),
                minefields=minefields,
                start_field=start_field,
                generation_settings=settings,
            )
            await on_completed(generation_id, board)
            return generation_id

        async def get_generation_status(self, generation_id):
            return self._statuses.get(generation_id, "completed")

    generator = ImmediateBoardGenerator()

    def _override():
        return generator

    api.dependency_overrides[LocalBoardGenerator] = _override
    yield
    api.dependency_overrides.pop(LocalBoardGenerator, None)
