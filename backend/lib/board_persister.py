import logging
import uuid

from backend.core.board import Board
from backend.db.db import async_session_maker
from backend.lib.pending_boards import RedisPendingStore
from backend.lib.redis_client import get_redis
from backend.protocols.board_repo_protocol import BoardNotFound
from backend.repositories import BoardRepository

logger = logging.getLogger(__name__)


class BackgroundBoardPersister:
    async def on_board_generated(self, generation_id: uuid.UUID, board: Board):
        logger.debug(
            f"Background persisting board {board.id} for generation {generation_id}"
        )
        async with async_session_maker() as session:
            board_repo = BoardRepository(session)
            try:
                existing_board = await board_repo.get_board(
                    board.difficulty_level, board.minefields
                )
                board = existing_board
            except BoardNotFound:
                await board_repo.add_board(board)

        async for redis_client in get_redis():
            pending_store = RedisPendingStore(redis_client)
            await pending_store.mark_ready(generation_id, board.id)
