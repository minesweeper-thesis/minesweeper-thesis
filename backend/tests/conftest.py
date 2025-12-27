import os
import random
import uuid
from contextlib import asynccontextmanager, suppress

import pytest
from httpx import ASGITransport, AsyncClient
from httpx_ws import AsyncWebSocketSession, aconnect_ws
from httpx_ws.transport import ASGIWebSocketTransport
from sqlalchemy.exc import IntegrityError

from backend.core.board import Board, DifficultyLevel, GenerationSettings
from backend.lib.board_generator import AsyncBoardGenerator, BackgroundBoardGenerator
from backend.protocols.board_repo_protocol import BoardNotFound

os.environ["DATABASE_URL"] = "sqlite+aiosqlite://"

from backend.db import db
from backend.main import api, app, lifespan
from backend.repositories.board_repo import BoardRepository

db.engine.echo = False


async def create_or_get_board(
    difficulty: DifficultyLevel,
    minefields: list[tuple[int, int]],
    start_field: tuple[int, int],
    generation_settings: GenerationSettings,
) -> Board:
    async with db.async_session_maker() as session:
        repo = BoardRepository(session)
        with suppress(BoardNotFound):
            return await repo.get_board(
                difficulty_level=difficulty,
                minefields=minefields,
            )

        board = Board(
            id=uuid.uuid4(),
            minefields=minefields,
            start_field=start_field,
            generation_settings=generation_settings,
        )
        try:
            await repo.add_board(board)
            return board
        except IntegrityError:
            await session.rollback()
            return await repo.get_board(
                difficulty_level=difficulty,
                minefields=minefields,
            )


def generate_board_data(
    difficulty_level: DifficultyLevel,
) -> tuple[list[tuple[int, int]], tuple[int, int]]:

    rows = difficulty_level.rows
    cols = difficulty_level.columns
    mines = difficulty_level.mine_count

    rng = random.Random(0)
    start_field = (0, 0)
    cells = [(i, j) for i in range(rows) for j in range(cols) if (i, j) != start_field]
    minefields = sorted(rng.sample(cells, k=mines))
    return minefields, start_field


class HTTPClient:
    def __init__(self, test_app, auth_cookie: str | None = None):
        self._test_app = test_app
        self._auth_cookie = auth_cookie

    def _headers(self, extra_headers: dict | None = None) -> dict:
        if self._auth_cookie:
            headers = {"Cookie": f"auth={self._auth_cookie}"}
        else:
            headers = {"Cookie": ""}
        if extra_headers:
            headers.update(extra_headers)
        return headers

    @asynccontextmanager
    async def _client(self):
        transport = ASGITransport(self._test_app)
        async with AsyncClient(
            transport=transport, base_url="https://testserver/api"
        ) as client:
            yield client

    @asynccontextmanager
    async def _ws_client(self):
        transport = ASGIWebSocketTransport(self._test_app)
        async with AsyncClient(
            transport=transport, base_url="https://testserver/api"
        ) as client:
            yield client

    @asynccontextmanager
    async def ws(self, path: str = "/ws"):
        async with self._ws_client() as client:
            headers = (
                {"Cookie": f"auth={self._auth_cookie}"} if self._auth_cookie else {}
            )
            ws: AsyncWebSocketSession
            async with aconnect_ws(
                f"https://testserver/api{path}",
                client,
                headers=headers,
            ) as ws:
                yield ws

    async def _request(self, method: str, url: str, **kwargs):
        async with self._client() as client:
            kwargs["headers"] = self._headers(kwargs.get("headers"))
            func = getattr(client, method)
            return await func(url, **kwargs)

    async def get(self, url: str, **kwargs):
        return await self._request("get", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self._request("post", url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self._request("put", url, **kwargs)

    async def patch(self, url: str, **kwargs):
        return await self._request("patch", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self._request("delete", url, **kwargs)


class AuthenticatedClientBundle:
    def __init__(self, test_app, user_data: dict, auth_cookie: str):
        self._test_app = test_app
        self.user_data = user_data
        self.auth_cookie = auth_cookie
        self.user_id = None
        self._http = HTTPClient(test_app, auth_cookie)

    @property
    def http(self):
        return self._http

    async def set_user_id(self):
        if not self.user_id:
            resp = await self.http.get("/auth/me")
            if resp.status_code == 200:
                self.user_id = resp.json().get("id")
        return self.user_id

    @asynccontextmanager
    async def ws(self, path: str = "/ws"):
        async with self._http.ws(path) as ws:
            yield ws


@pytest.fixture(scope="session")
async def test_app():
    async with lifespan(app):
        yield app


@pytest.fixture
async def session():
    async with db.async_session_maker() as session:
        yield session


@pytest.fixture
async def client_no_auth(test_app):
    yield HTTPClient(test_app)


@pytest.fixture
async def authenticated_clients(request, test_app):
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

    bundles = []

    transport = ASGITransport(test_app)
    async with AsyncClient(
        transport=transport, base_url="https://testserver/api"
    ) as client:
        for user_data in users_data:
            reg_resp = await client.post(
                "/auth/register",
                json={
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "nickname": user_data["nickname"],
                    "settings": {},
                },
            )
            assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"

            login_resp = await client.post(
                "/auth/login",
                data={
                    "username": user_data["email"],
                    "password": user_data["password"],
                },
            )
            assert login_resp.status_code == 204, f"Login failed: {login_resp.text}"

            auth_cookie = login_resp.cookies.get("auth")
            assert auth_cookie, "Login did not set 'auth' cookie"

            bundle = AuthenticatedClientBundle(test_app, user_data, auth_cookie)
            await bundle.set_user_id()
            bundles.append(bundle)

    yield bundles


class ImmediateBoardGenerator:
    def __init__(self):
        pass

    async def generate_board(self, settings, on_completed):
        generation_id = uuid.uuid4()

        minefields, start_field = generate_board_data(settings.difficulty_level)

        board = await create_or_get_board(
            difficulty=settings.difficulty_level,
            minefields=minefields,
            start_field=start_field,
            generation_settings=settings,
        )

        await on_completed(generation_id, board)
        return generation_id


api.dependency_overrides[BackgroundBoardGenerator] = ImmediateBoardGenerator
api.dependency_overrides[AsyncBoardGenerator] = ImmediateBoardGenerator
