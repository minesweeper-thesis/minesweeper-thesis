import uuid
from dataclasses import dataclass
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
    scoreboard: SessionScoreboard


class MultiplayerSession:
    def __init__(
        self,
        id: uuid.UUID,
        lobby_id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        game_config: GameConfig,
        player_ids: list[uuid.UUID],
        rounds_number: int,
        rounds: list[MultiplayerRound] = None,  # type: ignore
    ):
        if rounds is None:
            rounds = []

        self.id = id
        self.lobby_id = lobby_id
        self.difficulty_level = difficulty_level
        self.game_config = game_config
        self.player_ids = player_ids
        self.rounds_number = rounds_number
        self.rounds: list[MultiplayerRound] = rounds
        self.current_round_index = -1

        self.events: dict[uuid.UUID, list[Any]] = defaultdict(list)
        self.ready_players: set[uuid.UUID] = set()

        self.ready_locked = False

        self.scoreboard: SessionScoreboard = SessionScoreboard(
            items=[
                SessionScoreItem(user_id=player_id, score=0) for player_id in player_ids
            ]
        )

    def is_started(self) -> bool:
        return len(self.rounds) > 0 and self.rounds[0].state == "playing"

    def add_round(self, round: MultiplayerRound):
        self.rounds.append(round)

    def set_player_ids(self, player_ids: list[uuid.UUID]) -> None:
        if self.is_started() or self.current_round_index != -1 or len(self.rounds) > 0:
            raise ValueError("Cannot change players after session setup")

        self.player_ids = player_ids
        self.ready_players.intersection_update(set(player_ids))

        existing = {item.user_id for item in self.scoreboard.items}
        removed = existing - set(player_ids)
        if removed:
            self.scoreboard.items = [
                item for item in self.scoreboard.items if item.user_id not in removed
            ]

        added = set(player_ids) - existing
        for user_id in added:
            self.scoreboard.items.append(SessionScoreItem(user_id=user_id, score=0))

    @property
    def _current_round(self) -> MultiplayerRound:
        if self.current_round_index == -1:
            raise RuntimeError("No round is currently active")
        return self.rounds[self.current_round_index]

    @property
    def next_round(self) -> MultiplayerRound:
        if self.current_round_index + 1 >= len(self.rounds):
            raise RuntimeError("No next round available")
        return self.rounds[self.current_round_index + 1]

    @property
    def is_next_round_available(self) -> bool:
        return self.current_round_index + 1 < len(self.rounds)

    def set_ready(self, user_id: uuid.UUID):
        if self.ready_locked:
            raise ValueError("Ready state is locked")
        self.ready_players.add(user_id)

    def cancel_ready(self, user_id: uuid.UUID):
        if self.ready_locked:
            raise ValueError("Ready state is locked")
        self.ready_players.discard(user_id)

    def all_players_ready(self) -> bool:
        return self.ready_players == set(self.player_ids)

    def clear_ready_players(self):
        self.ready_players.clear()

    def is_user_ready(self, user_id: uuid.UUID) -> bool:
        return user_id in self.ready_players

    def lock_ready(self):
        self.ready_locked = True

    def end_round(self, round_index: int) -> None:
        round = self.rounds[round_index]

        if round.state != "playing":
            return

        round.end()
        self._consume_round_events()

        self.clear_ready_players()
        self.ready_locked = False

        for item in round.scoreboard.items:
            for session_item in self.scoreboard.items:
                if session_item.user_id == item.user_id:
                    session_item.score += item.score
                    break

        if self.is_over():
            self.scoreboard.sort()
            for user_id in self.player_ids:
                self.events[user_id].append(
                    SessionOver(session_id=self.id, scoreboard=self.scoreboard)
                )

    def start_next_round(self, start_at: datetime):
        if self.current_round_index != -1:
            if not self._current_round.all_gameplays_finished():
                raise RuntimeError("Previous round is not over yet")

        self.current_round_index += 1
        session_scores = {item.user_id: item.score for item in self.scoreboard.items}
        self._current_round.start(start_at, session_scores)
        self._consume_round_events()

    def is_over(self) -> bool:
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

        if self._current_round.all_gameplays_finished():
            self.clear_ready_players()
            self.ready_locked = False

        if self.is_over():
            self.scoreboard.sort()
            for user_id in self.player_ids:
                self.events[user_id].append(
                    SessionOver(session_id=self.id, scoreboard=self.scoreboard)
                )

    def _consume_round_events(self) -> None:
        for user_id, events in self._current_round.consume_events().items():
            self.events[user_id].extend(events)

    def consume_events(self) -> dict[uuid.UUID, list[Any]]:
        events = self.events
        self.events = defaultdict(list)
        return events


__all__ = ["MultiplayerSession", "SessionOver"]
