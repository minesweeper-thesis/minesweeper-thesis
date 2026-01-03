import uuid
from collections import defaultdict
from datetime import timedelta
from typing import Any

from backend.core.board import DifficultyLevel
from backend.core.game import *
from backend.core.game.game_actions import GameAction
from backend.core.multi.config import GameConfig
from backend.core.multi.multi_gameplay import *
from backend.core.multi.round import *
from backend.core.multi.score import SessionScoreboard, SessionScoreItem
from backend.core.user import *


class ReadyChangeLocked(Exception):
    pass


class RoundNotAvailable(Exception):
    pass


class UserNotInSession(Exception):
    pass


class SessionAlreadyOver(Exception):
    pass


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

    def is_active(self) -> bool:
        started = len(self.rounds) > 0 and self.rounds[0].state != "not_started"
        locked = self.ready_locked
        over = self.is_over()
        return (started or locked) and not over

    def add_round(self, round: MultiplayerRound):
        self.rounds.append(round)

    def remove_player(self, user: User):
        self.ensure_user_in_session(user)
        self.player_ids.remove(user.id)
        self.ready_players.discard(user.id)

    @property
    def _current_round(self) -> MultiplayerRound:
        if self.current_round_index == -1:
            raise RoundNotAvailable()
        return self.rounds[self.current_round_index]

    @property
    def next_round_index(self) -> int:
        return self.current_round_index + 1

    @property
    def next_round(self) -> MultiplayerRound:
        if self.current_round_index + 1 >= len(self.rounds):
            raise RoundNotAvailable()
        return self.rounds[self.current_round_index + 1]

    def set_ready(self, user: User):
        self.ensure_user_in_session(user)

        if not self.can_change_ready(user):
            raise ReadyChangeLocked()
        self.ready_players.add(user.id)

    def cancel_ready(self, user: User):
        self.ensure_user_in_session(user)

        if not self.can_change_ready(user):
            raise ReadyChangeLocked()
        self.ready_players.discard(user.id)

    def all_players_ready(self) -> bool:
        return self.ready_players == set(self.player_ids)

    def is_user_ready(self, user: User) -> bool:
        self.ensure_user_in_session(user)

        return user.id in self.ready_players

    def lock_ready(self):
        self.ready_locked = True

    def timeout_round(self, round_index: int) -> None:
        if not self.rounds[round_index].ended_before_timeout:
            self.rounds[round_index].timeout()
            self._on_round_end()

    def _on_round_end(self) -> None:
        self.ready_players.clear()
        self.ready_locked = False

        self._consume_round_events()
        self._update_scoreboard(self._current_round)

        self.scoreboard.sort()

    def _update_scoreboard(self, round: MultiplayerRound) -> None:
        for round_item in round.scoreboard.items:
            for session_item in self.scoreboard.items:
                if session_item.user_id == round_item.user_id:
                    session_item.score = round_item.score
                    break

    def add_next_round(
        self, start_at: datetime, board: Board, player_ids: list[uuid.UUID]
    ) -> None:
        session_scores = {
            item.user_id: item.score
            for item in self.scoreboard.items
            if item.user_id in player_ids
        }
        round = create_multiplayer_round(
            session_id=self.id,
            round_index=len(self.rounds),
            round_time=timedelta(seconds=self.game_config.max_round_time),
            board=board,
            player_ids=player_ids,
            mode=self.game_config.game_mode,
            start_at=start_at,
            session_scores=session_scores,
        )
        self.rounds.append(round)
        self.current_round_index += 1

    def is_over(self) -> bool:
        return (
            len(self.rounds) == self.rounds_number
            and self.rounds[-1].all_gameplays_finished()
        )

    def get_user_game_state(self, user: User) -> GameState:
        self._ensure_user_in_round(user)
        gameplay = self._current_round.gameplays[user.id]
        return gameplay.get_game_state()

    def execute_action_for_user(self, user: User, action: GameAction) -> None:
        self._ensure_user_in_round(user)
        self._current_round.execute_action_for_user(user.id, action)
        self._consume_round_events()

        if self._current_round.all_gameplays_finished():
            self._on_round_end()

    def _consume_round_events(self) -> None:
        for user_id, events in self._current_round.consume_events().items():
            self.events[user_id].extend(events)

    def consume_events(self) -> dict[uuid.UUID, list[Any]]:
        events = self.events
        self.events = defaultdict(list)
        return events

    def ensure_user_in_session(self, user: User) -> None:
        if user.id not in self.player_ids:
            raise UserNotInSession()

    def _ensure_user_in_round(self, user: User) -> None:
        if user.id not in self._current_round.gameplays:
            raise UserNotInSession()

    def is_user_in_session(self, user: User) -> bool:
        return user.id in self.player_ids

    def can_change_ready(self, user: User) -> bool:
        self.ensure_user_in_session(user)

        if self.is_over():
            raise SessionAlreadyOver()

        return not self.ready_locked

    def toggle_ready(self, user: User) -> None:
        self.ensure_user_in_session(user)

        if self.is_user_ready(user):
            self.cancel_ready(user)
        else:
            self.set_ready(user)


__all__ = [
    "MultiplayerSession",
    "ReadyChangeLocked",
    "UserNotInSession",
    "SessionAlreadyOver",
]
