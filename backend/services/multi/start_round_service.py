import logging
import uuid
from typing import Annotated, Literal

from fastapi import Depends

from backend.core.game import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.multi.round_scheduler import RoundScheduler
from backend.services.multi.session_boards_preparer import SessionBoardsPreparer

logger = logging.getLogger(__name__)


class StartRoundService:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        lobby_transport_factory: LobbyTransportFactoryDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
        boards_preparer: Annotated[SessionBoardsPreparer, Depends()],
        pending_store: PendingBoardsStoreDep,
        session_runtime_store: SessionRuntimeStoreDep,
        session_lock: SessionLockDep,
    ):
        self.multi_repo = multi_repo
        self.lobby_transport_factory = lobby_transport_factory
        self.round_scheduler = round_scheduler
        self.boards_preparer = boards_preparer
        self.lobby_transport_factory = lobby_transport_factory
        self.session_lock = session_lock
        self.pending_store = pending_store
        self.session_runtime_store = session_runtime_store

    async def toggle_user_ready(
        self,
        user: User,
        lobby_id: uuid.UUID,
    ):
        logger.debug(f"User {user.id} toggling ready status in lobby {lobby_id}")
        session = await self.multi_repo.get_for_lobby(lobby_id)

        if session.is_user_ready(user):
            await self.cancel_user_ready(user, lobby_id)
        else:
            await self.set_user_ready(user, lobby_id)

    async def cancel_user_ready(self, user: User, lobby_id: uuid.UUID):
        logger.debug(f"User {user.id} cancelling ready status in lobby {lobby_id}")
        ready_changed = False

        session = await self.multi_repo.get_for_lobby(lobby_id)

        async with self.session_lock.acquire(session.id):
            session = await self.multi_repo.get_session(session.id)

            if not session.is_user_ready(user):
                return

            if session.can_change_ready(user):
                session.cancel_ready(user)
                await self.multi_repo.save_session(session)
                ready_changed = True

        if ready_changed:
            await self.round_scheduler.cancel_start(session.id)
            transport = self.lobby_transport_factory.get(lobby_id)
            next_round_index = session.current_round_index + 1
            await transport.broadcast(UserReady(user.id, next_round_index, ready=False))

    async def set_user_ready(self, user: User, lobby_id: uuid.UUID):
        logger.debug(f"User {user.id} setting ready status in lobby {lobby_id}")
        ready_changed = False
        all_ready = False

        session = await self.multi_repo.get_for_lobby(lobby_id)

        async with self.session_lock.acquire(session.id):
            session = await self.multi_repo.get_session(session.id)

            if session.can_change_ready(user):
                session.set_ready(user)
                await self.multi_repo.save_session(session)
                ready_changed = True
                all_ready = session.all_players_ready()

        if ready_changed:
            transport = self.lobby_transport_factory.get(lobby_id)
            next_round_index = session.current_round_index + 1
            await transport.broadcast(UserReady(user.id, next_round_index, ready=True))

            if all_ready:
                await self._on_all_ready(session)

    async def _on_all_ready(self, session: MultiplayerSession):
        logger.info(f"All players ready in session {session.id}, starting round")

        next_round_index = session.current_round_index + 1
        difficulty_level = session.game_config.difficulty_level
        message = RoundReady(session.id, next_round_index, difficulty_level)

        transport = self.lobby_transport_factory.get(session.lobby_id)
        await transport.broadcast(message)

        is_generating = await self.session_runtime_store.is_generating(session.id)

        if len(session.rounds) == 0 and not is_generating:
            logger.info(f"Preparing boards for first round in session {session.id}")
            await self.boards_preparer.prepare(session)
            session = await self.multi_repo.get_session(session.id)

        if session.is_next_round_available:
            logger.info(f"Scheduling start of next round in session {session.id}")
            await self.round_scheduler.schedule_start(session)
        else:
            logger.info(
                f"No next round available in session {session.id}, waiting for boards"
            )
            await self.boards_preparer.wait_and_schedule_next_round(session.id)

    async def get_session_state(self, user: User, lobby_id: uuid.UUID):
        logger.debug(f"get_session_state(lobby_id={lobby_id})")

        session = await self.multi_repo.get_for_lobby(lobby_id)

        current_idx = session.current_round_index
        if current_idx == -1:
            round_index = 0
        elif session.rounds[current_idx].state == "playing":
            round_index = current_idx
        else:
            round_index = current_idx + 1

        board_ready = round_index < len(session.rounds)
        is_generating = await self.session_runtime_store.is_generating(session.id)
        schedule = await self.session_runtime_store.get_round_schedule(session.id)

        round_state: Literal[
            "not_ready", "generating", "countdown", "ready_lock", "playing"
        ]

        if board_ready and session.rounds[round_index].state == "playing":
            round_state = "playing"
        elif session.ready_locked:
            round_state = "ready_lock"
        elif not board_ready and is_generating:
            round_state = "generating"
        elif session.all_players_ready() and board_ready:
            round_state = "countdown"
        else:
            round_state = "not_ready"

        round_data = SessionStateRoundData(
            round_number=round_index + 1,
            schedule=schedule,
            state=round_state,
        )

        session_state = SessionState(session.id, round_data, session.scoreboard)

        transport = self.lobby_transport_factory.get(session.lobby_id)
        await transport.send(user.id, session_state)


__all__ = ["StartRoundService"]
