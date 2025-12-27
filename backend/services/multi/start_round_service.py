import logging
import uuid
from typing import Annotated

from fastapi import BackgroundTasks, Depends

logger = logging.getLogger(__name__)

from backend.core.game import *
from backend.core.multi import *
from backend.core.user import User
from backend.di.dependencies import *
from backend.di.session_lock import SessionLockDep
from backend.services.dto import *
from backend.services.exceptions import *
from backend.services.multi.round_scheduler import RoundScheduler
from backend.services.multi.session_boards_preparer import SessionBoardsPreparer


class StartRoundService:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        background_tasks: BackgroundTasks,
        lobby_transport_factory: LobbyTransportFactoryDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
        boards_preparer: Annotated[SessionBoardsPreparer, Depends()],
        pending_store: PendingBoardsStoreDep,
        session_lock: SessionLockDep,
    ):
        self.multi_repo = multi_repo
        self.background_tasks = background_tasks
        self.lobby_transport_factory = lobby_transport_factory
        self.round_scheduler = round_scheduler
        self.boards_preparer = boards_preparer
        self.lobby_transport_factory = lobby_transport_factory
        self.session_lock = session_lock
        self.pending_store = pending_store

    def _get_transport(self, lobby_id: uuid.UUID):
        return self.lobby_transport_factory.create(lobby_id)

    def _ensure_user_in_session(self, session: MultiplayerSession, user: User):
        if user.id not in session.player_ids:
            raise UserNotInSession()

        if session.is_over():
            raise SessionAlreadyOver()

    async def toggle_user_ready(
        self,
        user: User,
        lobby_id: uuid.UUID,
    ):
        logger.debug(f"User {user.id} toggling ready status in lobby {lobby_id}")
        session = await self.multi_repo.get_for_lobby(lobby_id)
        assert session is not None, "Session not found"

        self._ensure_user_in_session(session, user)
        if session.is_user_ready(user.id):
            await self.cancel_user_ready(user, lobby_id)
        else:
            await self.set_user_ready(user, lobby_id)

    async def cancel_user_ready(self, user: User, lobby_id: uuid.UUID):
        logger.debug(f"User {user.id} cancelling ready status in lobby {lobby_id}")
        should_notify = False

        session = await self.multi_repo.get_for_lobby(lobby_id)
        assert session is not None, "Session not found"

        async with self.session_lock.acquire(session.id):
            session = await self.multi_repo.get_session(session.id)
            assert session is not None, "Session not found"

            self._ensure_user_in_session(session, user)

            if session.is_user_ready(user.id) and not session.ready_locked:
                session.cancel_ready(user.id)
                await self.multi_repo.save_session(session)
                should_notify = True

        if should_notify:
            transport = self._get_transport(lobby_id)
            next_round_index = session.current_round_index + 1
            await transport.broadcast(UserNotReady(user.id, next_round_index))

    async def set_user_ready(self, user: User, lobby_id: uuid.UUID):
        logger.debug(f"User {user.id} setting ready status in lobby {lobby_id}")
        should_notify = False
        all_ready = False

        session = await self.multi_repo.get_for_lobby(lobby_id)
        assert session is not None, "Session not found"

        async with self.session_lock.acquire(session.id):
            session = await self.multi_repo.get_session(session.id)
            assert session is not None, "Session not found"

            self._ensure_user_in_session(session, user)

            if not session.is_user_ready(user.id) and not session.ready_locked:
                session.set_ready(user.id)
                await self.multi_repo.save_session(session)
                should_notify = True
                all_ready = session.all_players_ready()

        if should_notify:
            transport = self._get_transport(lobby_id)
            next_round_index = session.current_round_index + 1
            await transport.broadcast(UserReady(user.id, next_round_index))

            if all_ready:
                await self._on_all_ready(session)

    async def _on_all_ready(self, session: MultiplayerSession):
        logger.info(f"All players ready in session {session.id}, starting round")

        next_round_index = session.current_round_index + 1
        difficulty_level = session.game_config.difficulty_level
        message = RoundReady(session.id, next_round_index, difficulty_level)

        transport = self._get_transport(session.lobby_id)
        await transport.broadcast(message)

        is_pending = await self.pending_store.get_pending_round(session.id, 0)

        if len(session.rounds) == 0 and not is_pending:
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


__all__ = ["StartRoundService"]
