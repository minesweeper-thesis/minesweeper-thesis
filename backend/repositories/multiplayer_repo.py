import logging
import uuid
from typing import Optional

from redis.asyncio import Redis
from sqlalchemy import select

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.multi.session import MultiplayerSession
from backend.db.db import DBSession
from backend.lib.redis_client import decode, encode

from .orm import *


class MultiplayerSessionNotFound(Exception):
    pass


class RedisMultiplayerRepository(protocols.MultiplayerRepository):
    def __init__(self, session: DBSession, redis: Redis):
        self.session = session
        self.redis = redis
        self.prefix = "multi_session:"
        self.pending_prefix = "multi_pending:"

    async def get_session(self, session_id: uuid.UUID) -> MultiplayerSession:
        logger.debug(f"get_session(session_id={session_id})")
        pending_data = await self.redis.get(f"{self.pending_prefix}{session_id}")
        if pending_data:
            session = decode(pending_data)
            logger.debug(
                f"Retrieved pending session {session_id}, current_round_index={session.current_round_index}"
            )
            return session

        data = await self.redis.get(f"{self.prefix}{session_id}")
        if not data:
            logger.warning(f"Multiplayer session {session_id} not found")
            raise MultiplayerSessionNotFound(
                f"Multiplayer session with id {session_id} not found"
            )
        session = decode(data)
        logger.debug(
            f"Retrieved multiplayer session {session_id}, current_round_index={session.current_round_index}"
        )
        return session

    async def save_session(self, session: MultiplayerSession):
        logger.debug(
            f"save_session(session_id={session.id}, current_round_index={session.current_round_index})"
        )

        if session.is_over():
            await self.delete_pending(session.id)
            await self._save_to_db(session)
        else:
            await self._save_pending(session)

        logger.info(
            f"Multiplayer session {session.id} saved with current_round_index={session.current_round_index}"
        )

    async def _save_pending(self, session: MultiplayerSession):
        logger.debug(
            f"save_pending(session_id={session.id}, lobby_id={session.lobby_id})"
        )
        data = encode(session)
        async with self.redis.pipeline() as pipe:
            await pipe.set(f"{self.pending_prefix}{session.id}", data)
            await pipe.set(
                f"{self.pending_prefix}lobby:{session.lobby_id}", encode(session.id)
            )
            await pipe.execute()
        logger.info(
            f"Pending multiplayer session {session.id} saved for lobby {session.lobby_id}"
        )

    async def get_for_lobby(self, lobby_id: uuid.UUID) -> Optional[MultiplayerSession]:
        logger.debug(f"get_pending_for_lobby(lobby_id={lobby_id})")
        session_id_bytes = await self.redis.get(
            f"{self.pending_prefix}lobby:{lobby_id}"
        )
        if session_id_bytes:
            session_id_str = decode(session_id_bytes)
            data = await self.redis.get(f"{self.pending_prefix}{session_id_str}")
            if data:
                return decode(data)
        return None

    async def delete_pending(self, session_id: uuid.UUID):
        logger.debug(f"delete_pending(session_id={session_id})")
        data = await self.redis.get(f"{self.pending_prefix}{session_id}")
        if data:
            session = decode(data)
            async with self.redis.pipeline() as pipe:
                await pipe.delete(f"{self.pending_prefix}{session_id}")
                await pipe.delete(f"{self.pending_prefix}lobby:{session.lobby_id}")
                await pipe.execute()

    async def _save_to_db(self, session: MultiplayerSession):
        check_stmt = select(MultiplayerSessionORM).where(
            MultiplayerSessionORM.id == session.id
        )
        check_result = await self.session.execute(check_stmt)
        if check_result.scalar_one_or_none():
            return

        logger.info(f"Saving finished session {session.id} to DB")

        diff_stmt = select(DifficultyLevelORM).where(
            DifficultyLevelORM.rows == session.difficulty_level.rows,
            DifficultyLevelORM.columns == session.difficulty_level.columns,
            DifficultyLevelORM.mine_count == session.difficulty_level.mine_count,
        )
        diff_result = await self.session.execute(diff_stmt)
        difficulty_orm = diff_result.scalar_one_or_none()

        if not difficulty_orm:
            difficulty_orm = DifficultyLevelORM(
                rows=session.difficulty_level.rows,
                columns=session.difficulty_level.columns,
                mine_count=session.difficulty_level.mine_count,
            )
            self.session.add(difficulty_orm)
            await self.session.flush()

        session_orm = MultiplayerSessionORM(
            id=session.id,
            difficulty_level_id=difficulty_orm.id,
            rounds_number=session.rounds_number,
            max_round_time=session.game_config.max_round_time,
            mode=GameModeEnum(session.game_config.game_mode),
        )

        users_stmt = select(UserORM).where(UserORM.id.in_(session.player_ids))
        users_result = await self.session.execute(users_stmt)
        users = users_result.scalars().all()
        session_orm.players = list(users)

        self.session.add(session_orm)

        for round in session.rounds:
            round_orm = MultiplayerRoundORM(
                session_id=session.id,
                round_index=round.round_index,
                board_id=round.board.id,
            )
            self.session.add(round_orm)

            for gameplay in round.gameplays.values():
                gameplay_orm = MultiplayerGameplayORM(
                    session_id=session.id,
                    round_index=round.round_index,
                    user_id=gameplay.user_id,
                    time=gameplay.time,
                    status=GameStatusEnum(gameplay.status),
                    result=GameResultEnum(gameplay.result) if gameplay.result else None,
                    revealed_cells=gameplay.revealed_cells,
                    flagged_cells=gameplay.flagged_cells,
                )
                self.session.add(gameplay_orm)

        await self.session.commit()
        logger.info(f"Session {session.id} saved to DB")
