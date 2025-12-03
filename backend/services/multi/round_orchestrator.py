from datetime import datetime, timedelta

from backend.core.multi import MultiplayerSession
from backend.core.multi.round import RoundEnd, RoundStart
from backend.core.multi.session import SessionOver
from backend.protocols import GameTransport, MultiplayerRepository, Scheduler
from backend.services.dto import GameOverResult

ROUND_START_DELAY = timedelta(seconds=10)


class RoundOrchestrator:
    def __init__(
        self,
        multi_repo: MultiplayerRepository,
        scheduler: Scheduler,
        game_transport: GameTransport,
    ):
        self.multi_repo = multi_repo
        self.scheduler = scheduler
        self.game_transport = game_transport

    async def end_round(self, session: MultiplayerSession):
        # todo: lock z handle game action

        print("round ended", session._current_round.state)

        if session._current_round.state != "playing":
            return

        print("weszlo")

        over_gameplays = session.end_current_round()
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

        for user_id in session.player_ids:
            await self.game_transport.send(
                user_id,
                RoundEnd(session_id=session.id, round=session.current_round_index),
            )

        if session.is_session_over():
            for user_id in session.player_ids:
                await self.game_transport.send(
                    user_id, SessionOver(session_id=session.id)
                )

        await self.multi_repo.save_session(session)

    async def start_round(
        self, start_at: datetime, session: MultiplayerSession, first_round: bool = False
    ):
        print("round started")

        if not first_round and not session.all_players_ready():
            return

        end_at = start_at + timedelta(seconds=session.max_round_time)

        session.start_next_round(start_at)

        for user_id in session.player_ids:
            await self.game_transport.send(
                user_id,
                RoundStart(
                    session_id=session.id,
                    round=session.current_round_index,
                    start_at=start_at,
                    end_at=end_at,
                    start_field=session._current_round.board.start_field,
                ),
            )

        print("no powinno zrobic schedule", end_at)
        self.scheduler.schedule(
            self.end_round, end_at, session=session
        )  # todo: save job id

        await self.multi_repo.save_session(session)


__all__ = ["RoundOrchestrator"]
