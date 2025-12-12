from typing import Annotated

from fastapi import Depends

from backend.core.multi import MultiplayerSession
from backend.di.dependencies import PendingBoardsStoreDep
from backend.services.multi.round_scheduler import RoundScheduler


class PendingBoardWaiter:
    def __init__(
        self,
        pending_store: PendingBoardsStoreDep,
        round_scheduler: Annotated[RoundScheduler, Depends()],
    ):
        self.pending_store = pending_store
        self.round_scheduler = round_scheduler

    async def wait_and_schedule_next_round(
        self, session: MultiplayerSession, timeout_seconds: int
    ):
        next_round_index = session.current_round_index + 1

        pending = await self.pending_store.get_pending_round(
            session.id, next_round_index
        )
        if pending is None:
            raise RuntimeError("Pending board not found")

        await self.pending_store.wait_for_ready(pending.generation_id, timeout_seconds)

        await self.round_scheduler.schedule_start(session)


__all__ = ["PendingBoardWaiter"]
