import asyncio
import time
import uuid
from datetime import datetime
from typing import Annotated, Any, Awaitable, Callable

from fastapi import BackgroundTasks, Depends
from fastapi.concurrency import run_in_threadpool

from backend import repositories
from backend.core.game import *
from backend.core.multiplayer import ROUND_START_DELAY
from backend.core.user import User
from backend.lib.auth import CurrentUser
from backend.lib.pending_sessions import pending_sessions_store
from backend.repositories.exceptions import *
from backend.services.exceptions import *
from backend.services.lobby_service import (
    GameReadyMessage,
    RoundEndMessage,
    RoundStartMessage,
    SessionOverMessage,
)

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]

type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


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

        self.on_session_end_callback: Optional[Callable[[], Awaitable[None]]] = None

    async def set_session(
        self,
        session_id: uuid.UUID,
        user: CurrentUser,
        notify: Notify,
    ):
        self.session_id = session_id
        self.user_id = user.id

        self.notify = notify

        if not pending_sessions_store.is_pending(session_id):
            session = await self.multiplayer_repo.get_session(session_id)

            if user.id not in session.player_ids:
                raise ValueError("User is not part of this session")

        # dodac player_id do pending session

    async def handle_game_action(self, action: GameAction) -> ActionResult:
        session = await self.multiplayer_repo.get_session(self.session_id)

        result = session.handle_game_action(action, self.user_id)

        if session.rounds[session.current_round_index].is_round_over():
            session.end_current_round()
            gameplays = session.rounds[session.current_round_index].gameplays
            for user_id, gameplay in gameplays.items():
                if gameplay.loss_cause == LossCause("time_out"):
                    game_over_data = GameOverResult(
                        result="loss",
                        full_board=gameplay._gameplay.grid.grid,
                        elapsed_time=gameplay.time,
                        loss_cause=gameplay.loss_cause,
                    )
                    await self.notify(user_id, game_over_data)

            for user_id in session.player_ids:
                data = RoundEndMessage(
                    session_id=self.session_id,
                    round=session.current_round_index,
                )
                await self.notify(user_id, data)

        await self.multiplayer_repo.save_session(session)

        return result

    async def is_session_over(self) -> bool:
        session = await self.multiplayer_repo.get_session(self.session_id)

        return session.is_session_over()

    async def _end_round(self):
        print(f"[LOG] Ending round for session {self.session_id}")
        session = await self.multiplayer_repo.get_session(self.session_id)
        session.end_current_round()
        await self.multiplayer_repo.save_session(session)
        gameplays = session.rounds[session.current_round_index].gameplays
        for user_id, gameplay in gameplays.items():
            if gameplay.loss_cause == LossCause("time_out"):
                game_over_data = GameOverResult(
                    result="loss",
                    full_board=gameplay._gameplay.grid.grid,
                    elapsed_time=gameplay.time,
                    loss_cause=gameplay.loss_cause,
                )
                await self.notify(user_id, game_over_data)

        if session.is_session_over():
            data: Any = SessionOverMessage(session_id=self.session_id)
        else:
            data = RoundEndMessage(
                session_id=self.session_id,
                round=session.current_round_index,
            )

        for user_id in session.player_ids:
            await self.notify(user_id, data)

        if session.is_session_over() and self.on_session_end_callback:
            await self.on_session_end_callback()

    def _schedule_end_round(self, end_at: int):
        end_str = datetime.fromtimestamp(end_at).strftime("%Y-%m-%d %H:%M:%S")

        print(f"[LOG] Scheduling end round task to run at {end_str}")
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
            session.start_next_round(start_at, end_at)

            asyncio.run(self.multiplayer_repo.save_session(session))
            print(
                f"[LOG] Started round {session.current_round_index} for session {session_id}, ending at {end_at}"
            )

            async def send_start():
                print(f"[LOG] Sending round start messages for session {session_id}")
                print(session.player_ids)
                for user_id in session.player_ids:
                    data = RoundStartMessage(
                        session_id=session_id,
                        round=session.current_round_index,
                        start_at=start_at,
                        end_at=end_at,
                        start_field=session.rounds[session.current_round_index]
                        .gameplays[user_id]
                        ._gameplay.start_field,
                    )
                    await self.notify(user_id, data)

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

            next_round = session.current_round_index + 1
            print(
                f"[LOG] All users ready for session {session_id}, starting round {next_round} at {start_at}"
            )
            asyncio.create_task(
                run_in_threadpool(self._start_next_round, session_id, start_at)
            )

            data = GameReadyMessage(
                session_id=session_id, round=next_round, start_at=start_at
            )
            for player_id in session.player_ids:
                await self.notify(player_id, data)
