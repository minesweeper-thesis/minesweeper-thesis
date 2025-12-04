import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.core.game.game_actions import GameAction
from backend.core.multi.config import GameConfig
from backend.core.multi.gameplay import *
from backend.core.multi.round import *
from backend.core.user import *


@dataclass
class SessionOver:
    session_id: uuid.UUID


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

        self.events: dict[uuid.UUID, list[Any]] = defaultdict(list)
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

    def cancel_ready(self, user_id: uuid.UUID):
        self.ready_players.discard(user_id)

    def all_players_ready(self) -> bool:
        return self.ready_players == set(self.player_ids)

    def clear_ready_players(self):
        self.ready_players.clear()

    def end_current_round(self) -> None:
        self._current_round.end()
        self._consume_round_events()

        if self.is_session_over():
            for user_id in self.player_ids:
                self.events[user_id].append(SessionOver(session_id=self.id))

    def start_next_round(self, start_at: datetime):
        if self.current_round_index != -1:
            if not self._current_round.all_gameplays_finished():
                raise RuntimeError("Previous round is not over yet")

        self.current_round_index += 1
        self._current_round.start(start_at)
        self._consume_round_events()

    def is_session_over(self) -> bool:
        return (
            len(self.rounds) == self.rounds_number
            and self.rounds[-1].all_gameplays_finished()
        )

    def get_user_game_state(self, user_id: uuid.UUID) -> GameState:
        gameplay = self._current_round.gameplays[user_id]
        return gameplay.get_game_state()

    def execute_action_for_user(self, user_id: uuid.UUID, action: GameAction) -> None:
        self._current_round.execute_action_for_user(user_id, action)
        self._consume_round_events()

        if self.is_session_over():
            for user_id in self.player_ids:
                self.events[user_id].append(SessionOver(session_id=self.id))

    def _consume_round_events(self) -> None:
        for user_id, events in self._current_round.consume_events().items():
            self.events[user_id].extend(events)

    def consume_events(self) -> dict[uuid.UUID, list[Any]]:
        events = self.events
        self.events = defaultdict(list)
        return events


__all__ = ["MultiplayerSession", "SessionOver"]
