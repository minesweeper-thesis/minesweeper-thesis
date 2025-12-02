import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, Optional, Protocol

from backend.core.board import Board
from backend.core.game import *
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


@dataclass
class RoundStartAwaiting:
    session_id: uuid.UUID
    round: int
    start_at: datetime


@dataclass
class RoundStartCanceled:
    session_id: uuid.UUID
    round: int


type RoundState = Literal["not_started", "countdown", "playing", "ended"]


class Clock(Protocol):
    def now(self) -> datetime: ...


class MultiplayerRound:
    def __init__(
        self,
        session_id: uuid.UUID,
        round_number: int,
        round_time: timedelta,
        board: Board,
        gameplays: list[MultiplayerGameplay],
        clock: Clock,
    ):
        self.session_id = session_id
        self.round_number = round_number
        self.round_time = round_time
        self.board = board
        self.gameplays = {gameplay.user_id: gameplay for gameplay in gameplays}
        self.ready_players: set[uuid.UUID] = set()
        self.clock = clock

        self.state: RoundState = "not_started"

        self.start_at: Optional[datetime] = None
        self.end_at: Optional[datetime] = None

        self.time_out_gameplays: list[MultiplayerGameplay] = []

        self.events: list[Any] = []

    def set_user_ready(self, user_id: uuid.UUID):
        self.ready_players.add(user_id)

        if self.ready_players == set(self.gameplays.keys()):
            self.state = "countdown"

            self.start_at = self.clock.now() + ROUND_START_DELAY
            self.end_at = self.start_at + self.round_time

            self.events.append(
                RoundStartAwaiting(
                    session_id=self.session_id,
                    round=self.round_number,
                    start_at=self.start_at,
                )
            )

    def cancel_user_ready(self, user_id: uuid.UUID):
        self.ready_players.discard(user_id)

        if self.state == "countdown":
            self.state = "not_started"
            self.start_at = None
            self.end_at = None

            self.events.append(
                RoundStartCanceled(
                    session_id=self.session_id,
                    round=self.round_number,
                )
            )

    def all_gameplays_finished(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def all_players_ready(self) -> bool:
        return self.ready_players == set(self.gameplays.keys())

    def should_start(self) -> bool:
        return (
            self.state == "countdown"
            and self.start_at is not None
            and self.clock.now() >= self.start_at
        )

    def start(self) -> RoundStart:
        if self.state != "not_started":
            raise RuntimeError("Round is started or ended already")

        self.start_at = self.clock.now()
        self.end_at = self.start_at + self.round_time

        self.state = "playing"

        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()

        return RoundStart(
            session_id=self.session_id,
            round=self.round_number,
            start_at=self.start_at,
            end_at=self.end_at,
            start_field=self.board.get_start_field(),
        )

    def end(self):
        if self.state != "playing":
            raise RuntimeError("Round is not in playing state")

        for gameplay in self.gameplays.values():
            if not gameplay.is_game_over():
                gameplay.finish_game("loss", loss_cause=LossCause("time_out"))
                self.time_out_gameplays.append(gameplay)

        return RoundEnd(
            session_id=self.session_id,
            round=self.round_number,
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
    clock: Clock,
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
        round_number=round_index,
        round_time=round_time,
        board=board,
        gameplays=gameplays,
        clock=clock,
    )
