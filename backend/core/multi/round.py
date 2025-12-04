import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from backend.core.board import Board
from backend.core.game import *
from backend.core.multi.gameplay import MultiplayerGameplay


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


type RoundState = Literal["not_started", "playing", "ended"]


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

        self._state: RoundState = "not_started"

        self.start_at: Optional[datetime] = None
        self.end_at: Optional[datetime] = None

        self._events: dict[uuid.UUID, list[Any]] = defaultdict(list)

    def all_gameplays_finished(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def start(self, start_at: datetime) -> None:
        if self._state != "not_started":
            raise RuntimeError("Round is started or ended already")

        self.start_at = start_at
        self.end_at = self.start_at + self.round_time

        self._state = "playing"

        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()

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
        if self._state != "playing":
            raise RuntimeError("Round is not in playing state")

        self._state = "ended"

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

        for user_id in self.gameplays.keys():
            self._events[user_id].append(
                RoundEnd(
                    session_id=self.session_id,
                    round_index=self.round_index,
                )
            )

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

        if self.all_gameplays_finished():
            self.end()

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
