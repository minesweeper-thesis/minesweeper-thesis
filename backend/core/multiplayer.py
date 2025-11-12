import time
import uuid
from typing import Callable, Literal, Optional

from pydantic import BaseModel

from backend.core.board import Board
from backend.core.game import *
from backend.core.singleplayer import SingleplayerGameplay


class OpponentState(BaseModel):
    revealed_cnt: int
    result: Optional[GameResult]


type Notifier = Callable[[OpponentState], None]


class UserGameplayState(BaseModel):
    revealed_cells: list[tuple[int, int]]
    time: float
    result: Optional[GameResult]
    notify_me: Notifier


class HalfMultiGameplay(SingleplayerGameplay):
    def __init__(
        self,
        board: Board,
        revealed_cells: list[tuple[int, int]],
        status: GameStatus,
        result: Optional[GameResult],
        elapsed_time: float,
        mode: GameMode,
        notify_opponent: Notifier,
    ):
        super().__init__(
            uuid.uuid4(),
            board,
            revealed_cells,
            status,
            result,
            False,
            elapsed_time,
            mode,
        )
        self.notify_opponent = notify_opponent

    def _notify_opponent(self):
        my_state = OpponentState(
            revealed_cnt=len(self.revealed),
            result=self.result,
        )
        self.notify_opponent(my_state)

    def reveal_one(self, x: int, y: int):
        super().reveal_one(x, y)
        self._notify_opponent()

    def reveal_many(self, x: int, y: int):
        super().reveal_many(x, y)
        self._notify_opponent()


class MultiplayerGameplay:
    def __init__(
        self,
        id: uuid.UUID,
        board: Board,
        mode: GameMode,
        user1_state: UserGameplayState,
        user2_state: UserGameplayState,
        status: GameStatus,
    ):
        self.id = id
        self.user1_state = user1_state
        self.user2_state = user2_state
        self.board = board
        self.mode = mode
        self.status: GameStatus = status
        self._time_start = None

        self.user1_gameplay = HalfMultiGameplay(
            board,
            user1_state.revealed_cells,
            status,
            user1_state.result,
            user1_state.time,
            mode,
            user2_state.notify_me,
        )
        self.user2_gameplay = HalfMultiGameplay(
            board,
            user2_state.revealed_cells,
            status,
            user2_state.result,
            user2_state.time,
            mode,
            user1_state.notify_me,
        )
        self.start_field = board.start_field

    def play_as(self, user_number: Literal[1, 2]) -> SingleplayerGameplay:
        if user_number == 1:
            return self.user1_gameplay
        elif user_number == 2:
            return self.user2_gameplay
        else:
            raise ValueError("Invalid user number")

    def start(self):
        if self.status == "not_started":
            self.play_as(1).start_game_if_not_started()
            self.play_as(2).start_game_if_not_started()
            self._time_start = time.monotonic()
            self.play_as(1)._time_start = self._time_start
            self.play_as(2)._time_start = self._time_start
