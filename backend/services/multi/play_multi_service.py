import uuid

from fastapi import BackgroundTasks

from backend.core.game import *
from backend.di.dependencies import *
from backend.lib.auth import CurrentUser
from backend.protocols.game_transport_protocol import GameTransport
from backend.repositories.exceptions import *
from backend.services.exceptions import *


class PlayMultiService:
    def __init__(
        self,
        board_repo: BoardRepositoryDep,
        lobby_repo: LobbyRepositoryDep,
        multi_repo: MultiplayerRepositoryDep,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystemDep,
        scheduler: SchedulerDep,
        game_transport_factory: GameTransportFactoryDep,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = scheduler
        self.game_transport_factory = game_transport_factory

        self.transport: GameTransport = None  # type: ignore

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

        if self.session.is_session_over():
            raise ValueError("Session is already over")

        self.transport = self.game_transport_factory.create(session_id)

    def is_session_over(self) -> bool:
        return self.session.is_session_over()

    async def get_game_state(self):
        game_state = self.session.get_user_game_state(self.user.id)
        await self.transport.send(self.user.id, game_state)

    async def execute_action(self, action: GameAction):
        self.session.execute_action_for_user(self.user.id, action)

        for user_id, events in self.session.consume_events().items():
            for event in events:
                await self.transport.send(user_id, event)

        await self.multi_repo.save_session(self.session)


__all__ = ["PlayMultiService"]
