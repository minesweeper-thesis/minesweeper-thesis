import logging
import uuid
from datetime import timedelta
from typing import Optional

from backend.core.board import Board
from backend.core.multi import create_multiplayer_round
from backend.db import async_session_maker
from backend.lib.redis_client import get_redis_client
from backend.lib.session_lock import SessionLock
from backend.lib.session_runtime_store import RedisSessionRuntimeStore
from backend.protocols.repos.exceptions import BoardNotFound, SessionNotFound

logger = logging.getLogger(__name__)


class BackgroundRoundHandler:
    async def on_board_generated(
        self, session_id: uuid.UUID, generation_id: Optional[uuid.UUID], board: Board
    ):
        from backend.repositories import BoardRepository, RedisMultiplayerRepository

        logger.debug(
            f"Background handling board {board.id} for session {session_id} (generation {generation_id})"
        )

        redis_client = await get_redis_client()
        session_lock = SessionLock(redis_client)

        async with async_session_maker() as db_session:
            board_repo = BoardRepository(db_session)
            multi_repo = RedisMultiplayerRepository(db_session, redis_client)
            session_runtime_store = RedisSessionRuntimeStore(redis_client)

            try:
                existing_board = await board_repo.get_board(
                    board.difficulty_level, board.minefields
                )
                board = existing_board
            except BoardNotFound:
                await board_repo.add_board(board)

            async with session_lock.acquire(session_id):
                try:
                    session = await multi_repo.get_session(session_id)
                except SessionNotFound:
                    logger.warning(
                        f"Session {session_id} not found during background board generation"
                    )
                    return

                round_time = timedelta(seconds=session.game_config.max_round_time)
                round = await create_multiplayer_round(
                    session_id=session.id,
                    round_index=len(session.rounds),
                    round_time=round_time,
                    board=board,
                    player_ids=session.player_ids,
                    mode=session.game_config.game_mode,
                )

                session.add_round(round)
                await multi_repo.save_session(session)
                await session_runtime_store.notify_round_ready(session_id)

                if generation_id:
                    await session_runtime_store.remove_pending_generation(
                        session_id, generation_id
                    )

                logger.info(
                    f"Added round {round.round_index} to session {session_id} in background"
                )
