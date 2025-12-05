import uuid
from collections.abc import Callable
from datetime import timedelta
from typing import Annotated, Any, Awaitable

from fastapi import BackgroundTasks, Depends

from backend import protocols, repositories
from backend.core.game import *
from backend.core.multi import *
from backend.core.user import User
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.lib.pending_boards import get_pending_boards_store
from backend.lib.scheduler import get_scheduler
from backend.lib.websocket_game_transport import WebSocketGameTransport
from backend.repositories.exceptions import *
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.multi.round_scheduler import RoundScheduler

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
Scheduler = Annotated[protocols.Scheduler, Depends(get_scheduler)]
GameTransport = Annotated[
    protocols.GameTransport, Depends(lambda: WebSocketGameTransport())
]
PendingBoardsStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]

type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


ROUND_START_DELAY = timedelta(seconds=5)


class StartRoundService:
    def __init__(
        self,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        multi_repo: MultiplayerRepository,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystem,
        scheduler: Scheduler,
        game_transport: GameTransport,
        pending_store: PendingBoardsStore,
        round_scheduler: Annotated[RoundScheduler, Depends()],
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport = game_transport
        self.pending_store = pending_store
        self.round_scheduler = round_scheduler

        self.messages: list[tuple[uuid.UUID, Any]] = []

    async def toggle_user_ready(self, session_id: uuid.UUID, user: User):
        session = await self.multi_repo.get_session(session_id)
        if session.is_user_ready(user):
            await self._cancel_user_ready(session, user)
        else:
            await self.set_user_ready(session_id, user)

    async def cancel_user_ready(self, session_id: uuid.UUID, user: User):
        session = await self.multi_repo.get_session(session_id)
        await self._cancel_user_ready(session, user)

    async def _cancel_user_ready(self, session: MultiplayerSession, user: User):
        if user.id not in session.player_ids:
            raise PermissionError("User is not part of this session")

        if session.is_session_over():
            raise ValueError("Session is already over")

        if session.ready_locked:
            return

        if not session.is_user_ready(user):
            return

        session.cancel_ready(user.id)

        for player_id in session.player_ids:
            await self.game_transport.send(
                player_id, UserNotReady(user.id, session.current_round_index + 1)
            )

        await self.multi_repo.save_session(session)

    async def set_user_ready(self, session_id: uuid.UUID, user: User):
        session = await self.multi_repo.get_session(session_id)

        if user.id not in session.player_ids:
            raise PermissionError("User is not part of this session")

        if session.is_session_over():
            raise ValueError("Session is already over")

        if session.ready_locked:
            return

        if session.is_user_ready(user):
            return

        session.set_ready(user.id)

        next_round_index = session.current_round_index + 1

        for player_id in session.player_ids:
            await self.game_transport.send(
                player_id, UserReady(user.id, next_round_index)
            )

        if session.all_players_ready():
            for user_id in session.player_ids:
                await self.game_transport.send(
                    user_id,
                    RoundReady(session.id, next_round_index),
                )

            if session.is_next_round_available:
                countdown_to = datetime.now() + ROUND_START_DELAY
                round_start_time = countdown_to + ROUND_START_DELAY

                for user_id in session.player_ids:
                    await self.game_transport.send(
                        user_id,
                        RoundCountdown(
                            session.id,
                            next_round_index,
                            countdown_to,
                            round_start_time,
                            session._next_round.board.start_field,
                        ),
                    )

                self.scheduler.schedule(
                    self.round_scheduler.lock_ready,
                    countdown_to,
                    session_id=session.id,
                )

                self.scheduler.schedule(
                    self.round_scheduler.start_round,
                    round_start_time,
                    start_at=round_start_time,
                    session_id=session.id,
                )
            else:
                self.background_tasks.add_task(
                    self._wait_for_generation_and_start_round, session
                )

        await self.multi_repo.save_session(session)

    async def _wait_for_generation_and_start_round(self, session: MultiplayerSession):
        next_round_index = session.current_round_index + 1

        pending = await self.pending_store.get_pending_round(
            session.id, next_round_index
        )
        if pending is None:
            raise RuntimeError("Pending board not found")

        await self.pending_store.wait_for_ready(pending.generation_id, 24 * 3600)

        countdown_to = datetime.now() + ROUND_START_DELAY
        start_at = countdown_to + ROUND_START_DELAY

        for user_id in session.player_ids:
            await self.game_transport.send(
                user_id,
                RoundCountdown(
                    session.id,
                    next_round_index,
                    countdown_to,
                    start_at,
                    session._next_round.board.start_field,
                ),
            )

        self.scheduler.schedule(
            self.round_scheduler.lock_ready,
            countdown_to,
            session_id=session.id,
        )

        self.scheduler.schedule(
            self.round_scheduler.start_round,
            start_at,
            session_id=session.id,
            start_at=start_at,
        )

    def collect_messages(self) -> list[tuple[uuid.UUID, Any]]:
        msgs = self.messages
        self.messages = []
        return msgs


__all__ = ["StartRoundService"]
