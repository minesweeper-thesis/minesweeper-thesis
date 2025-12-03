import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, Optional

from backend.core.board import Board
from backend.core.game import *
from backend.core.game.game_actions import GameAction
from backend.core.multi.gameplay import MultiplayerGameplay

ROUND_START_DELAY = timedelta(seconds=10)


@dataclass
class RoundStart:
    session_id: uuid.UUID
    round: int
    start_at: datetime
    end_at: datetime
    start_field: Cell


@dataclass
class RoundEnd:
    session_id: uuid.UUID
    round: int


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

        self.state: RoundState = "not_started"

        self.start_at: Optional[datetime] = None
        self.end_at: Optional[datetime] = None

        self.time_out_gameplays: list[MultiplayerGameplay] = []

        self.events: list[Any] = []

    def all_gameplays_finished(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def start(self, start_at: datetime) -> None:
        if self.state != "not_started":
            raise RuntimeError("Round is started or ended already")

        self.start_at = start_at
        self.end_at = self.start_at + self.round_time

        self.state = "playing"

        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()

        self.events.append(
            RoundStart(
                session_id=self.session_id,
                round=self.round_index,
                start_at=self.start_at,
                end_at=self.end_at,
                start_field=self.board.start_field,
            )
        )

    def end(self) -> None:
        if self.state != "playing":
            raise RuntimeError("Round is not in playing state")

        for gameplay in self.gameplays.values():
            if not gameplay.is_game_over():
                gameplay.finish_game("loss", loss_cause=LossCause("time_out"))
                self.time_out_gameplays.append(gameplay)

        self.events.append(
            RoundEnd(
                session_id=self.session_id,
                round=self.round_index,
            )
        )

    def execute_action_for_user(self, user_id: uuid.UUID, action: GameAction) -> None:
        gameplay = self.gameplays[user_id]
        self.events.append(action.execute(gameplay))

        if gameplay.is_game_over():
            assert gameplay.result is not None
            self.events.append(
                GameOverResult(
                    result=gameplay.result,
                    full_board=gameplay._gameplay.grid.grid,
                    elapsed_time=gameplay.elapsed_time,
                    loss_cause=gameplay.loss_cause,
                )
            )

    def get_events(self) -> list[Any]:
        events = self.events
        self.events = []
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
