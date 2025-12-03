import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.core.multi.config import GameConfig
from backend.core.multi.gameplay import *
from backend.core.multi.round import *
from backend.core.user import *


@dataclass
class SessionOver:
    session_id: uuid.UUID


type MultiplayerSessionActionResult = (
    RoundStart | RoundEnd | SessionOver | RoundStartCanceled | None
)


ROUND_START_DELAY = timedelta(seconds=10)


class MultiplayerSession:
    def __init__(
        self,
        id: uuid.UUID,
        lobby_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        game_config: GameConfig,
        max_round_time: int,
        player_ids: list[uuid.UUID],
        clock: Clock,
        rounds_number: int,
        rounds: list[MultiplayerRound] = [],
    ):
        self.id = id
        self.lobby_id = lobby_id
        self.difficulty_level = difficulty_level
        self.game_config = game_config
        self.max_round_time = max_round_time
        self.player_ids = player_ids
        self.rounds_number = rounds_number
        self.rounds: list[MultiplayerRound] = rounds
        self.current_round_index = -1
        self.clock = clock

        self.events: list[Any] = []
        self.ready_players: set[uuid.UUID] = set()

    def add_round(self, round: MultiplayerRound):
        self.rounds.append(round)

    @property
    def _current_round(self) -> MultiplayerRound:
        if self.current_round_index == -1:
            raise RuntimeError("No round is currently active")
        return self.rounds[self.current_round_index]

    @property
    def _next_round(self) -> MultiplayerRound:
        if self.current_round_index + 1 >= len(self.rounds):
            raise RuntimeError("No next round available")
        return self.rounds[self.current_round_index + 1]

    @property
    def is_next_round_available(self) -> bool:
        return self.current_round_index + 1 < len(self.rounds)

    def set_ready(self, user_id: uuid.UUID):
        self.ready_players.add(user_id)

        # if self.ready_players == set(self.player_ids):
        #     self.state = "countdown"

        #     self.start_at = self.clock.now() + ROUND_START_DELAY
        #     self.end_at = self.start_at + self._next_round.round_time

        #     self.events.append(
        #         RoundStartAwaiting(
        #             session_id=self.id,
        #             round=self._next_round.round_index,
        #             start_at=self.start_at,
        #         )
        #     )
        # self.events.extend(self._next_round.get_events())

    def cancel_ready(self, user_id: uuid.UUID):
        self.ready_players.discard(user_id)

        # if self.state == "countdown":
        #     self.state = "not_started"
        #     self.start_at = None
        #     self.end_at = None

        #     self.events.append(
        #         RoundStartCanceled(
        #             session_id=self.id,
        #             round=self._next_round.round_index,
        #         )
        #     )
        # self.events.extend(self._next_round.get_events())

    def all_players_ready(self) -> bool:
        return self.ready_players == set(self.player_ids)

    def clear_ready_players(self):
        self.ready_players.clear()

    def end_current_round(
        self,
    ) -> list[tuple[uuid.UUID, MultiplayerGameplay]]:
        round_end = self._current_round.end()
        self.events.append(round_end)

        over_gameplays_data = []

        for gameplay in self._current_round.time_out_gameplays:
            over_gameplays_data.append((gameplay.user_id, gameplay))

        if self.is_session_over():
            self.events.append(SessionOver(session_id=self.id))

        return over_gameplays_data

    def all_gameplays_finished(self) -> bool:
        return self._current_round.all_gameplays_finished()

    def start_next_round(self, start_at: datetime):
        if self.current_round_index != -1:
            if not self._current_round.all_gameplays_finished():
                raise RuntimeError("Previous round is not over yet")

        self.current_round_index += 1
        print("Starting round", self.current_round_index)
        round_start = self._current_round.start(start_at)
        self.events.append(round_start)

    def is_session_over(self) -> bool:
        return (
            len(self.rounds) == self.rounds_number
            and self.rounds[-1].all_gameplays_finished()
        )

    def get_gameplay_for_user(self, user_id: uuid.UUID) -> MultiplayerGameplay:
        return self._current_round.gameplays[user_id]

    def get_events(self) -> list[Any]:
        events = self.events
        self.events = []
        return events


__all__ = ["MultiplayerSession", "MultiplayerSessionActionResult", "SessionOver"]
