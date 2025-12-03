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
PendingBoardsStore = Annotated[
    protocols.PendingBoardsStore, Depends(get_pending_boards_store)
]

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
        pending_store: PendingBoardsStore,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport = game_transport
        self.pending_store = pending_store

        self.messages: list[tuple[uuid.UUID, Any]] = []

        self.orchestrator = RoundOrchestrator(
            multi_repo=self.multi_repo,
            scheduler=self.scheduler,
            game_transport=self.game_transport,
        )

    async def set_user_ready(self, session_id: uuid.UUID, user: User):
        session = await self.multi_repo.get_session(session_id)

        if user.id not in session.player_ids:
            raise PermissionError("User is not part of this session")

        session.set_ready(user.id)

        if session.all_players_ready():
            if session.is_next_round_available:
                round_start_time = datetime.now() + ROUND_START_DELAY

                # todo: notify

                self.scheduler.schedule(
                    self.orchestrator.start_round,
                    round_start_time,
                    start_at=round_start_time,
                    session=session,  # todo: zmienic na id
                )
            else:
                self.background_tasks.add_task(
                    self.wait_for_generation_and_start_round, session
                )

        # for event in session.get_events():
        #     for player_id in session.player_ids:
        #         self.messages.append((player_id, event))

        await self.multi_repo.save_session(session)

    async def wait_for_generation_and_start_round(self, session: MultiplayerSession):
        next_round_index = session.current_round_index + 1

        pending = await self.pending_store.get_pending_round(
            session.id, next_round_index
        )
        if pending is None:
            raise RuntimeError("Pending board not found")

        await self.pending_store.wait_for_ready(pending.generation_id, 24 * 3600)

        start_at = datetime.now() + ROUND_START_DELAY

        self.scheduler.schedule(
            self.orchestrator.start_round,
            start_at,
            start_at=start_at,
            session=session,  # todo: zmienic na id
        )

    def collect_messages(self) -> list[tuple[uuid.UUID, Any]]:
        msgs = self.messages
        self.messages = []
        return msgs


__all__ = ["StartRoundUseCase"]
