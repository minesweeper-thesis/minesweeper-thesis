import asyncio
import uuid
from collections.abc import Callable
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Annotated, Any, Awaitable

from fastapi import BackgroundTasks, Depends

from backend import repositories
from backend.core.game import *
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import (
    MultiplayerSessionAction,
    RoundAwaiting,
    RoundReadyCanceled,
    SessionOver,
    create_multiplayer_session,
)
from backend.core.user import User
from backend.lib.auth import CurrentUser
from backend.lib.notification_system import NotificationSystem as Notifications
from backend.lib.notification_system import get_notification_system
from backend.lib.pending_sessions import pending_sessions_store
from backend.lib.scheduler import async_scheduler
from backend.repositories.exceptions import *
from backend.services.exceptions import *

MultiplayerRepository = Annotated[repositories.MultiplayerRepository, Depends()]
BoardRepository = Annotated[repositories.BoardRepository, Depends()]
LobbyRepository = Annotated[repositories.LobbyRepository, Depends()]

NotificationSystem = Annotated[Notifications, Depends(get_notification_system)]
type MultiplayerAction = MultiplayerSessionAction | GameAction
type MultiplayerResult = RoundStart | RoundEnd | GameActionResult | RoundAwaiting | RoundReadyCanceled | SessionOver


class MultiplayerGameTransport(Protocol):
    async def receive(self) -> MultiplayerAction: ...
    async def send(self, user_id: uuid.UUID, result: MultiplayerResult) -> None: ...
    async def close(self) -> None: ...


type Notify = Callable[[uuid.UUID, Any], Awaitable[None]]


ROUND_START_DELAY = timedelta(seconds=10)


class MultiplayerService:
    def __init__(
        self,
        board_repo: BoardRepository,
        lobby_repo: LobbyRepository,
        multi_repo: MultiplayerRepository,
        background_tasks: BackgroundTasks,
        notification_system: NotificationSystem,
    ):
        self.multi_repo = multi_repo
        self.board_repo = board_repo
        self.lobby_repo = lobby_repo
        self.background_tasks = background_tasks
        self.notification_system = notification_system
        self.scheduler = async_scheduler

    async def set_session(
        self,
        session_id: uuid.UUID,
        user: CurrentUser,
        transport: MultiplayerGameTransport,
    ):
        self.session_id = session_id
        self.user = user

        self.transport = transport

        while (
            pending_sessions_store.is_pending(session_id)
            and pending_sessions_store.get(session_id).status != "ready"  # type: ignore
        ):
            await asyncio.sleep(0.1)

        pending_sessions_store.remove(session_id)

        self.session = await self.multi_repo.get_session(session_id)

        if self.user.id not in self.session.player_ids:
            raise ValueError("User is not part of this session")

    async def session_loop(self):
        while True:
            message = await self.transport.receive()

            if isinstance(message, MultiplayerSessionAction):
                await self.handle_multiplayer_session_action(message)
                continue

            with suppress(ValueError):
                await self.handle_game_action(message)

                if self.session.is_session_over():
                    await self.transport.close()
                    return

    async def handle_multiplayer_session_action(
        self,
        action: MultiplayerSessionAction,
    ):
        result = action.handle(self.session, self.user.id)

        if isinstance(result, RoundAwaiting):
            self.scheduler.schedule(self._start_next_round, result.start_at, result)
            for player_id in self.session.player_ids:
                await self.transport.send(player_id, result)

        await self.multi_repo.save_session(self.session)

    async def handle_game_action(self, action: GameAction):
        result = self.session.handle_game_action(action, self.user.id)
        await self.transport.send(self.user.id, result)

        if self.session.is_current_round_over():
            data, over_gameplays = self.session.end_current_round()

            for user_id, game_over_data in over_gameplays:
                await self.transport.send(user_id, game_over_data)

        await self.multi_repo.save_session(self.session)

        if self.session.is_current_round_over():
            for user_id in self.session.player_ids:
                await self.transport.send(user_id, data)

    async def _end_round(self):  # todo: lock z handle game action
        if self.session.is_current_round_over():
            return

        data, over_gameplays = self.session.end_current_round()
        for user_id, game_over_data in over_gameplays:
            await self.transport.send(user_id, game_over_data)

        for user_id in self.session.player_ids:
            await self.transport.send(user_id, data)

        if self.session.is_session_over():
            await self.transport.close()

        await self.multi_repo.save_session(self.session)

    async def _start_next_round(self, round_awaiting: RoundAwaiting):
        start_at = round_awaiting.start_at

        if self.session.all_users_ready():
            end_at = start_at + timedelta(seconds=self.session.max_round_time)
            data = self.session.start_next_round(start_at)

            for user_id in self.session.player_ids:
                await self.transport.send(user_id, data)

            self.scheduler.schedule(self._end_round, end_at)

        await self.multi_repo.save_session(self.session)

    async def set_user_ready(self):
        round_awaiting = self.session.set_ready(self.user.id)

        if round_awaiting is not None:
            self.scheduler.schedule(
                self._start_next_round, round_awaiting.start_at, round_awaiting
            )
            for player_id in self.session.player_ids:
                await self.transport.send(player_id, round_awaiting)

        await self.multi_repo.save_session(self.session)

    async def set_user_ready_in_lobby(
        self,
        lobby_id: uuid.UUID,
        user: User,
        game_notify: Notify,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        lobby.set_user_ready(user)
        self.lobby_repo.save_lobby(lobby)

        if lobby.all_users_ready():
            start_at = datetime.now() + ROUND_START_DELAY

            session_id = uuid.uuid4()
            pending_sessions_store.add(session_id, [u.id for u in lobby.users])

            self.scheduler.schedule(
                self._create_game_session,
                start_at,
                session_id=session_id,
                lobby_id=lobby.id,
                start_at=start_at,
                game_notify=game_notify,
            )

            event = RoundAwaiting(session_id=session_id, round=0, start_at=start_at)
            for lobby_user in lobby.users:
                await self.notification_system.notify(lobby_user.id, event)

    async def _create_game_session(
        self,
        session_id: uuid.UUID,
        lobby_id: uuid.UUID,
        start_at: datetime,
        game_notify: Notify,
    ):
        lobby = self.lobby_repo.get_lobby(lobby_id)
        if lobby.all_users_ready():
            for user in lobby.users:
                lobby.set_user_not_ready(user)

            session = await create_multiplayer_session(
                session_id,
                lobby.game_config,
                [user.id for user in lobby.users],
            )

            end_at = start_at + timedelta(seconds=session.max_round_time)
            event = session.start_next_round(start_at)

            await self.multi_repo.save_session(session)

            pending_sessions_store.mark_ready(session_id)

            print("start sent")
            for user_id in session.player_ids:
                await game_notify(user_id, event)

            self.session_id = session_id
            self.scheduler.schedule(self._end_round, end_at, game_notify=game_notify)
        else:
            pending_sessions_store.remove(session_id)
