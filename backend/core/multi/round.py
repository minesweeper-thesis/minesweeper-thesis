import uuid
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from backend.core.board import Board
from backend.core.game import *
from backend.core.multi.gameplay import MultiplayerGameplay
from backend.core.multi.score import *


@dataclass
class RoundStart:
    session_id: uuid.UUID
    round_index: int
    start_at: datetime
    end_at: datetime
    start_field: Cell


@dataclass
class RoundEnd:
    session_id: uuid.UUID
    round_index: int
    scoreboard: RoundScoreboard


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
    ):
        self.session_id = session_id
        self.round_index = round_index
        self.round_time = round_time
        self.board = board
        self.gameplays = {gameplay.user_id: gameplay for gameplay in gameplays}

        self.state: RoundState = "not_started"

        self.start_at: Optional[datetime] = None
        self.end_at: Optional[datetime] = None

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

    def all_gameplays_finished(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def start(self, start_at: datetime, session_scores: dict[uuid.UUID, float]) -> None:
        if self.state != "not_started":
            raise InvalidRoundState(current_state=self.state)

        self.start_at = start_at
        self.end_at = self.start_at + self.round_time

        self.state = "playing"

        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()

        for user_id, score in session_scores.items():
            score_item = self._get_user_score_item(user_id)
            score_item.score = score
            score_item.status = "in_progress"

        for user_id in self.gameplays.keys():
            self._events[user_id].append(
                RoundStart(
                    session_id=self.session_id,
                    round_index=self.round_index,
                    start_at=self.start_at,
                    end_at=self.end_at,
                    start_field=self.board.start_field,
                )
            )

    def end(self) -> None:
        if self.state != "playing":
            raise InvalidRoundState(current_state=self.state)

        self.state = "ended"

        for gameplay in self.gameplays.values():
            if not gameplay.is_game_over():
                gameplay.finish_game("loss", loss_cause=LossCause("time_out"))
                self._events[gameplay.user_id].append(
                    GameOverResult(
                        result="loss",
                        full_board=gameplay._gameplay.grid.grid,
                        elapsed_time=gameplay.elapsed_time,
                        loss_cause=gameplay.loss_cause,
                    )
                )

        for gameplay in self.gameplays.values():
            self._update_user_score_item(gameplay.user_id)
            self._set_final_score(gameplay.user_id)

        for user_id in self.gameplays.keys():
            self.scoreboard.sort()
            self._events[user_id].append(
                RoundEnd(
                    session_id=self.session_id,
                    round_index=self.round_index,
                    scoreboard=self.scoreboard,
                )
            )

    def _get_user_score_item(self, user_id: uuid.UUID) -> RoundScoreItem:
        for item in self.scoreboard.items:
            if item.user_id == user_id:
                return item
        raise RuntimeError(f"User {user_id} not found in scoreboard")

    def _update_user_score_item(self, user_id: uuid.UUID):
        gameplay = self.gameplays[user_id]
        score_item = self._get_user_score_item(user_id)

        score_item.revealed_count = len(gameplay.revealed_cells)
        score_item.status = "finished" if gameplay.is_game_over() else "in_progress"
        score_item.result = gameplay.result
        score_item.loss_cause = gameplay.loss_cause

    def _set_final_score(self, user_id: uuid.UUID):
        gameplay = self.gameplays[user_id]
        score_item = self._get_user_score_item(user_id)

        if gameplay.is_game_over() and gameplay.result == "win":
            score_item.score += self.round_time.total_seconds() - gameplay.elapsed_time

    def execute_action_for_user(self, user_id: uuid.UUID, action: GameAction) -> None:
        gameplay = self.gameplays[user_id]
        self._events[user_id].append(action.execute(gameplay))

        if gameplay.is_game_over():
            assert gameplay.result is not None
            self._events[user_id].append(
                GameOverResult(
                    result=gameplay.result,
                    full_board=gameplay._gameplay.grid.grid,
                    elapsed_time=gameplay.elapsed_time,
                    loss_cause=gameplay.loss_cause,
                )
            )

        if not self.all_gameplays_finished():
            before = copy(self._get_user_score_item(user_id))
            self._update_user_score_item(user_id)
            after = self._get_user_score_item(user_id)
            if before != after:
                for player_id in self.gameplays.keys():
                    self._events[player_id].append(ScoreUpdate(score=after))

    def consume_events(self) -> dict[uuid.UUID, list[Any]]:
        events = self._events
        self._events = defaultdict(list)
        return events


async def create_multiplayer_round(
    session_id: uuid.UUID,
    round_index: int,
    round_time: timedelta,
    board: Board,
    player_ids: list[uuid.UUID],
    mode: GameMode,
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
    )
