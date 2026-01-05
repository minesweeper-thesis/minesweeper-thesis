import uuid
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Literal

from backend.core.board import Board
from backend.core.game import *
from backend.core.multi.multi_gameplay import MultiplayerGameplay
from backend.core.multi.score import *


@dataclass
class ScoreUpdate:
    score: RoundScoreItem


type RoundState = Literal["not_started", "playing", "ended"]


class InvalidRoundState(Exception):
    def __init__(self, current_state: RoundState):
        self.current_state = current_state
        super().__init__(f"Invalid round state: {current_state}")


class MultiplayerRound:
    def __init__(
        self,
        session_id: uuid.UUID,
        round_index: int,
        round_time: timedelta,
        board: Board,
        gameplays: list[MultiplayerGameplay],
        start_at: datetime,
        session_scores: dict[uuid.UUID, float],
        timer: Callable[[], datetime] = datetime.now,
    ):
        self.session_id = session_id
        self.round_index = round_index
        self.round_time = round_time
        self.board_id = board.id
        self.gameplays = {gameplay.user_id: gameplay for gameplay in gameplays}

        self._start_at = start_at
        self._end_at = start_at + round_time
        self._timer = timer
        self.ended_before_timeout = False
        self._events: dict[uuid.UUID, list[Any]] = defaultdict(list)

        self.scoreboard: RoundScoreboard = RoundScoreboard(
            items=[
                RoundScoreItem(
                    user_id=gameplay.user_id,
                    score=0,
                    revealed_count=0,
                    status="not_started",
                )
                for gameplay in gameplays
            ]
        )

        for user_id, score in session_scores.items():
            score_item = self._get_user_score_item(user_id)
            score_item.score = score
            score_item.status = "in_progress"

        for gameplay in gameplays:
            gameplay.start_game_if_not_started(start_at)

    @property
    def state(self) -> RoundState:
        now = self._timer()
        if now < self._start_at:
            return "not_started"
        if self._start_at <= now < self._end_at and not self.all_gameplays_finished():
            return "playing"
        return "ended"

    def all_gameplays_finished(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def timeout(self) -> None:
        for gameplay in self.gameplays.values():
            if not gameplay.is_game_over():
                gameplay.finish_game(
                    "loss", LossCause("time_out"), now=self._end_at.timestamp()
                )
                self._events[gameplay.user_id].append(
                    GameOverResult(
                        result="loss",
                        full_board=gameplay._gameplay.grid.grid,
                        elapsed_time=gameplay.elapsed_time,
                        loss_cause=gameplay.loss_cause,
                    )
                )

        for gameplay in self.gameplays.values():
            self._update_user_score(gameplay.user_id)

        self.scoreboard.sort()

    def _get_user_score_item(self, user_id: uuid.UUID) -> RoundScoreItem:
        for item in self.scoreboard.items:
            if item.user_id == user_id:
                return item
        raise RuntimeError(f"User {user_id} not found in scoreboard")

    def _update_user_score(self, user_id: uuid.UUID):
        gameplay = self.gameplays[user_id]
        score_item = self._get_user_score_item(user_id)
        before = deepcopy(score_item)

        score_item.revealed_count = len(gameplay.revealed_cells)
        score_item.status = "finished" if gameplay.is_game_over() else "in_progress"
        score_item.result = gameplay.result
        score_item.loss_cause = gameplay.loss_cause

        if gameplay.is_game_over() and gameplay.result == "win":
            score_item.score += self.round_time.total_seconds() - gameplay.elapsed_time

        if before != score_item:
            for player_id in self.gameplays.keys():
                self._events[player_id].append(ScoreUpdate(score=score_item))

    def execute_action_for_user(self, user_id: uuid.UUID, action: GameAction) -> None:
        if self.state != "playing":
            raise InvalidRoundState(current_state=self.state)

        gameplay = self.gameplays[user_id]
        self._events[user_id].append(action.execute(gameplay))

        self._update_user_score(user_id)

        if gameplay.is_game_over():
            if self.all_gameplays_finished():
                self.ended_before_timeout = True

            assert gameplay.result is not None
            self._events[user_id].append(
                GameOverResult(
                    result=gameplay.result,
                    full_board=gameplay._gameplay.grid.grid,
                    elapsed_time=gameplay.elapsed_time,
                    loss_cause=gameplay.loss_cause,
                )
            )

            self.scoreboard.sort()

    def consume_events(self) -> dict[uuid.UUID, list[Any]]:
        events = self._events
        self._events = defaultdict(list)
        return events


def create_multiplayer_round(
    session_id: uuid.UUID,
    round_index: int,
    round_time: timedelta,
    board: Board,
    player_ids: list[uuid.UUID],
    mode: GameMode,
    start_at: datetime,
    session_scores: dict[uuid.UUID, float],
) -> MultiplayerRound:
    gameplays = [
        MultiplayerGameplay(
            user_id=player_id,
            board=board,
            mode=mode,
        )
        for player_id in player_ids
    ]

    return MultiplayerRound(
        session_id=session_id,
        round_index=round_index,
        round_time=round_time,
        board=board,
        gameplays=gameplays,
        start_at=start_at,
        session_scores=session_scores,
    )


__all__ = [
    "MultiplayerRound",
    "create_multiplayer_round",
    "ScoreUpdate",
    "RoundState",
    "InvalidRoundState",
]
