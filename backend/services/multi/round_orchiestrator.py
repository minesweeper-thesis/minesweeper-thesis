from datetime import datetime, timedelta

from backend.core.multi import MultiplayerSession
from backend.services.dto import GameOverResult
from backend.services.protocols import GameTransport, MultiplayerRepository, Scheduler

ROUND_START_DELAY = timedelta(seconds=10)


class RoundOrchestrator:
    def __init__(
        self,
        session: MultiplayerSession,
        multi_repo: MultiplayerRepository,
        scheduler: Scheduler,
        game_transport: GameTransport,
    ):
        self.session = session
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.game_transport = game_transport

    async def end_round(self):
        # todo: lock z handle game action

        if self.session._current_round.state != "in_progress":
            return

        over_gameplays = self.session.end_current_round()
        for user_id, gameplay in over_gameplays:
            await self.game_transport.send(
                user_id,
                GameOverResult(
                    result="loss",
                    full_board=gameplay._gameplay.grid.grid,
                    elapsed_time=gameplay.time,
                    loss_cause=gameplay.loss_cause,
                ),
            )

        for event in self.session.get_events():
            for user_id in self.session.player_ids:
                await self.game_transport.send(user_id, event)

        await self.multi_repo.save_session(self.session)

    async def start_round(self, start_at: datetime):
        if not self.session.all_players_ready():
            return

        end_at = start_at + timedelta(seconds=self.session.max_round_time)

        self.session.start_next_round()

        for data in self.session.get_events():
            for user_id in self.session.player_ids:
                await self.game_transport.send(user_id, data)

        self.scheduler.schedule(self.end_round, end_at)

        await self.multi_repo.save_session(self.session)


__all__ = ["RoundOrchestrator"]
