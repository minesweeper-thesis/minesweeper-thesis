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
from backend.lib.scheduler import get_scheduler
from backend.lib.websocket_game_transport import WebSocketGameTransport
from backend.repositories.exceptions import *
from backend.services.dto import GameActionResult
from backend.services.exceptions import *
from backend.services.multi import RoundOrchestrator

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
Scheduler = Annotated[protocols.Scheduler, Depends(get_scheduler)]
GameTransport = Annotated[
    protocols.GameTransport, Depends(lambda: WebSocketGameTransport())
]


type MultiplayerResult = RoundStart | RoundEnd | RoundStartAwaiting | RoundStartCanceled | SessionOver | GameActionResult


type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


ROUND_START_DELAY = timedelta(seconds=10)


class StartRoundUseCase:
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

        self.messages: list[tuple[uuid.UUID, Any]] = []

    async def set_user_ready(self, session_id: uuid.UUID, user: User):
        self.session = await self.multi_repo.get_session(session_id)

        if user.id not in self.session.player_ids:
            raise PermissionError("User is not part of this session")

        self.session.set_ready(user.id)

        orchestrator = RoundOrchestrator(
            session=self.session,
            multi_repo=self.multi_repo,
            scheduler=self.scheduler,
            game_transport=self.game_transport,
        )

        if self.session._next_round.should_start():
            self.scheduler.schedule(
                orchestrator.start_round,
                self.session._next_round.start_at,
                start_at=self.session._next_round.start_at,
            )

        for event in self.session.get_events():
            for player_id in self.session.player_ids:
                self.messages.append((player_id, event))

        await self.multi_repo.save_session(self.session)

    def collect_messages(self) -> list[tuple[uuid.UUID, Any]]:
        msgs = self.messages
        self.messages = []
        return msgs


__all__ = ["StartRoundUseCase"]
