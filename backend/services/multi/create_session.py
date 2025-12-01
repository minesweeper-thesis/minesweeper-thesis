import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Annotated, Any, Awaitable

from fastapi import BackgroundTasks, Depends

from backend import repositories
from backend.core.game import *
from backend.core.lobby import create_session
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import (
    Clock,
    RoundStartAwaiting,
    RoundStartCanceled,
    SessionOver,
)
from backend.core.user import User
from backend.infra.notification_system import NotificationSystem as Notifications
from backend.infra.notification_system import get_notification_system
from backend.infra.scheduler import get_scheduler
from backend.infra.websocket_game_transport import WebSocketGameTransport
from backend.repositories.exceptions import *
from backend.services import protocols
from backend.services.dto import GameActionResult
from backend.services.exceptions import *
from backend.services.multi.round_orchiestrator import RoundOrchestrator

MultiplayerRepository = Annotated[
    protocols.MultiplayerRepository, Depends(repositories.MultiplayerRepository)
]
BoardRepository = Annotated[
    protocols.BoardRepository, Depends(repositories.BoardRepository)
]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
Scheduler = Annotated[protocols.Scheduler, Depends(get_scheduler)]
GameTransport = Annotated[
    protocols.GameTransport, Depends(lambda: WebSocketGameTransport())
]


type MultiplayerResult = RoundStart | RoundEnd | RoundStartAwaiting | RoundStartCanceled | SessionOver | GameActionResult


type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


ROUND_START_DELAY = timedelta(seconds=10)


class ClockImpl(Clock):
    def now(self) -> datetime:
        return datetime.now()


class CreateMultiplayerSessionUseCase:
    def __init__(
        self,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        multi_repo: MultiplayerRepository,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystem,
        scheduler: Scheduler,
        game_transport: GameTransport,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport = game_transport

    async def set_user_ready_in_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        if lobby.all_users_ready():
            start_at = datetime.now() + ROUND_START_DELAY

            session_id = uuid.uuid4()
            # pending_sessions_store.add(session_id, [u.id for u in lobby.users])

            self.scheduler.schedule(
                self._create_game_session,
                start_at,
                session_id=session_id,
                lobby_id=lobby.id,
                start_at=start_at,
            )

            event = RoundStartAwaiting(
                session_id=session_id, round=0, start_at=start_at
            )
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, event)

    async def _create_game_session(
        self,
        session_id: uuid.UUID,
        lobby_id: uuid.UUID,
        start_at: datetime,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if lobby.all_users_ready():
            lobby.reset_ready_for_new_session()
            self.session = await create_session(session_id, lobby, ClockImpl())

            end_at = start_at + timedelta(seconds=self.session.max_round_time)
            self.session.start_next_round()

            await self.multi_repo.save_session(self.session)

            # pending_sessions_store.mark_ready(session_id)

            orchestrator = RoundOrchestrator(
                self.session,
                self.multi_repo,
                self.scheduler,
                self.game_transport,
            )

            for event in self.session.get_events():
                for user_id in self.session.player_ids:
                    await self.game_transport.send(user_id, event)

            self.session_id = session_id
            self.scheduler.schedule(orchestrator.end_round, end_at)
        else:
            pass
            # pending_sessions_store.remove(session_id)


__all__ = ["CreateMultiplayerSessionUseCase"]
