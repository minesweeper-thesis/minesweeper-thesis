import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from backend.core.board import Board
from backend.core.game import *
from backend.core.multi.gameplay import MultiplayerGameplay


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
    time_out_gameplays: list[MultiplayerGameplay] = field(default_factory=list)


type RoundState = Literal["not_started", "playing", "ended"]


class MultiplayerRound:
    def __init__(
        self,
        session_id: uuid.UUID,
        round_number: int,
        round_time: timedelta,
        board: Board,
        gameplays: list[MultiplayerGameplay],
    ):
        self.session_id = session_id
        self.round_number = round_number
        self.round_time = round_time
        self.board = board
        self.gameplays = {gameplay.user_id: gameplay for gameplay in gameplays}
        self.ready_players: set[uuid.UUID] = set()

        self.state: RoundState = "not_started"

        self.start_at: datetime = None  # type: ignore
        self.end_at: datetime = None  # type: ignore

    def handle_game_action(
        self, action: GameAction, user_id: uuid.UUID
    ) -> GameActionResult:
        if self.state != "playing":
            raise RuntimeError("Round has not started yet")

        return action.handle(self.gameplays[user_id])

    def is_round_over(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def start(self, start_at: datetime) -> RoundStart:
        if self.state != "not_started":
            raise RuntimeError("Round is started or ended already")

        self.state = "playing"

        self.start_at = start_at
        self.end_at = start_at + self.round_time

        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()

        return RoundStart(
            session_id=self.session_id,
            round=self.round_number,
            start_at=start_at,
            end_at=self.end_at,
            start_field=self.board.start_field,
        )

    def end(self):
        if self.state != "playing":
            raise RuntimeError("Round is not in playing state")

        time_out_gameplays = []

        for gameplay in self.gameplays.values():
            if not gameplay.is_game_over():
                gameplay.finish_game("loss", loss_cause=LossCause("time_out"))
                time_out_gameplays.append(gameplay)

        return RoundEnd(
            session_id=self.session_id,
            round=self.round_number,
            time_out_gameplays=time_out_gameplays,
        )


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
            notify_opponents=lambda state: None,
        )
        for player_id in player_ids
    ]

    return MultiplayerRound(
        session_id=session_id,
        round_number=round_index,
        round_time=round_time,
        board=board,
        gameplays=gameplays,
    )
