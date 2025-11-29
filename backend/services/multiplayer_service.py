import asyncio
import time
import uuid
from contextlib import suppress
from typing import Annotated

from fastapi import BackgroundTasks, Depends
from fastapi.concurrency import run_in_threadpool

from backend import repositories
from backend.core.game import *
from backend.core.multi import ROUND_START_DELAY
from backend.core.multi.session import (
    CancelReadyMessage,
    MultiplayerResult,
    ReadyMessage,
)
from backend.core.user import User
from backend.lib.auth import CurrentUser
from backend.lib.pending_sessions import pending_sessions_store
from backend.repositories.exceptions import *
from backend.services.exceptions import *

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]

type MultiplayerAction = ReadyMessage | CancelReadyMessage | GameAction


class MultiplayerGameTransport(Protocol):
    async def receive(self) -> MultiplayerAction: ...
    async def send(self, user_id: uuid.UUID, result: MultiplayerResult) -> None: ...
    async def close(self) -> None: ...


class MultiplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        multiplayer_repo: MultiplayerRepository,
        background_tasks: BackgroundTasks,
    ):
        self.multiplayer_repo = multiplayer_repo
        self.board_repo = board_repo
        self.background_tasks = background_tasks

    async def set_session(
        self,
        session_id: uuid.UUID,
        user: CurrentUser,
        transport: MultiplayerGameTransport,
    ):
        self.session_id = session_id
        self.user_id = user.id
        self.user = user

        self.transport = transport

        if pending_sessions_store.is_pending(session_id):
            session = pending_sessions_store.get(session_id)  # type: ignore
        else:
            session = await self.multiplayer_repo.get_session(session_id)  # type: ignore

        if user.id not in session.player_ids:  # type: ignore
            raise ValueError("User is not part of this session")

    async def session_loop(self):
        while True:
            message = await self.transport.receive()

            if isinstance(message, ReadyMessage):
                await self.set_user_ready(self.session_id, self.user)
                continue

            if isinstance(message, CancelReadyMessage):
                # await self.set_user_not_ready(self.session_id, self.user)
                continue

            with suppress(ValueError):
                action_result = await self.handle_game_action(message)
                await self.transport.send(self.user_id, action_result)

                session = await self.multiplayer_repo.get_session(self.session_id)

                if session.is_session_over():
                    await self.transport.close()
                    return

    async def handle_game_action(self, action: GameAction) -> GameActionResult:
        session = await self.multiplayer_repo.get_session(self.session_id)

        result = session.handle_game_action(action, self.user_id)

        if session.current_round.is_round_over():
            data, over_gameplays = session.end_current_round()

            for user_id, game_over_data in over_gameplays:
                await self.transport.send(user_id, game_over_data)

        await self.multiplayer_repo.save_session(session)

        if session.current_round.is_round_over():
            for user_id in session.player_ids:
                await self.transport.send(user_id, data)

        return result

    async def is_session_over(self) -> bool:
        session = await self.multiplayer_repo.get_session(self.session_id)

        return session.is_session_over()

    async def _end_round(self):
        session = await self.multiplayer_repo.get_session(self.session_id)
        data, over_gameplays = session.end_current_round()

        for user_id, game_over_data in over_gameplays:
            await self.transport.send(user_id, game_over_data)

        await self.multiplayer_repo.save_session(session)

        for user_id in session.player_ids:
            await self.transport.send(user_id, data)

        if session.is_session_over():
            await self.transport.close()

    def _schedule_end_round(self, end_at: int):
        delay = end_at - int(time.time())
        if delay > 0:
            time.sleep(delay)
        asyncio.run(self._end_round())

    def _start_next_round(self, session_id: uuid.UUID, start_at: int):
        current = time.time()
        diff = start_at - current
        time.sleep(diff)

        session = asyncio.run(self.multiplayer_repo.get_session(session_id))

        if session.all_users_ready():
            end_at = start_at + session.max_round_time
            data = session.start_next_round(start_at, end_at)

            asyncio.run(self.multiplayer_repo.save_session(session))

            async def send_start():
                for user_id in session.player_ids:
                    await self.transport.send(user_id, data)

            asyncio.run(send_start())
            self._schedule_end_round(end_at)

    async def set_user_ready(
        self,
        session_id: uuid.UUID,
        user: User,
    ):
        session = await self.multiplayer_repo.get_session(session_id)
        session.set_ready(user.id)
        await self.multiplayer_repo.save_session(session)

        if session.all_users_ready():
            start_at = int(time.time()) + ROUND_START_DELAY

            asyncio.create_task(
                run_in_threadpool(self._start_next_round, session_id, start_at)
            )

            event = session.start_countdown(start_at)
            for player_id in session.player_ids:
                await self.transport.send(player_id, event)
