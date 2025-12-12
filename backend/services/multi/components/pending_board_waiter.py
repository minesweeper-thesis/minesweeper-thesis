import uuid
from typing import Annotated

from fastapi import Depends

from backend.di.dependencies import MultiplayerRepositoryDep, PendingBoardsStoreDep
from backend.services.multi.round_scheduler import RoundScheduler


class PendingBoardWaiter:
    def __init__(
        self,
        multi_repo: MultiplayerRepositoryDep,
        pending_store: PendingBoardsStoreDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
    ):
        self.multi_repo = multi_repo
        self.pending_store = pending_store
        self.round_scheduler = round_scheduler

    async def wait_and_schedule_next_round(
        self, session_id: uuid.UUID, timeout_seconds: int
    ):
        session = await self.multi_repo.get_session(session_id)
        next_round_index = session.current_round_index + 1

        pending = await self.pending_store.get_pending_round(
            session.id, next_round_index
        )
        if pending is None:
            raise RuntimeError("Pending board not found")

        await self.pending_store.wait_for_ready(pending.generation_id, timeout_seconds)

        fresh_session = await self.multi_repo.get_session(session_id)
        await self.round_scheduler.schedule_start(fresh_session)


__all__ = ["PendingBoardWaiter"]
