import uuid
from collections.abc import Callable
from typing import Annotated, Any, Awaitable

from fastapi import BackgroundTasks, Depends

from backend import repositories
from backend.core.game import *
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import (
    RoundStartAwaiting,
    RoundStartCanceled,
    SessionOver,
)
from backend.infra.notification_system import NotificationSystem as Notifications
from backend.infra.notification_system import get_notification_system
from backend.infra.scheduler import get_scheduler
from backend.lib.auth import CurrentUser
from backend.repositories.exceptions import *
from backend.services import protocols
from backend.services.dto import GameActionResult, GameOverResult
from backend.services.exceptions import *
from backend.services.single.game_actions import GameAction

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
Scheduler = Annotated[protocols.Scheduler, Depends(get_scheduler)]

type MultiplayerResult = RoundStart | RoundEnd | RoundStartAwaiting | RoundStartCanceled | SessionOver | GameActionResult


type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


class PlayMultiUseCase:
    def __init__(
        self,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        multi_repo: MultiplayerRepository,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystem,
        scheduler: Scheduler,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler

        self.messages: list[tuple[uuid.UUID, Any]] = []

    async def set_session(
        self,
        session_id: uuid.UUID,
        user: CurrentUser,
    ):
        self.session_id = session_id
        self.user = user

        self.session = await self.multi_repo.get_session(session_id)

        if self.user.id not in self.session.player_ids:
            raise ValueError("User is not part of this session")

    def is_session_over(self) -> bool:
        return self.session.is_session_over()

    def get_game_state(self) -> GameState:
        gameplay = self.session.get_gameplay_for_user(self.user.id)
        return gameplay.get_game_state()

    async def execute_action(self, action: GameAction):
        result = action.execute(self.session.get_gameplay_for_user(self.user.id))

        self.messages.append((self.user.id, result))

        if self.session.all_gameplays_finished():
            over_gameplays = self.session.end_current_round()

            for user_id, game_over_data in over_gameplays:
                self.messages.append(
                    (
                        user_id,
                        GameOverResult(
                            result="loss",
                            full_board=game_over_data._gameplay.grid.grid,
                            elapsed_time=game_over_data.time,
                            loss_cause=game_over_data.loss_cause,
                        ),
                    )
                )

        for data in self.session.get_events():
            for user_id in self.session.player_ids:
                self.messages.append((user_id, data))

        await self.multi_repo.save_session(self.session)

    def collect_messages(self) -> list[tuple[uuid.UUID, Any]]:
        msgs = self.messages
        self.messages = []
        return msgs


__all__ = ["PlayMultiUseCase", "Notify"]
