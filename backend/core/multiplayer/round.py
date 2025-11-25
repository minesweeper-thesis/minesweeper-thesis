import time
import uuid
from datetime import datetime

from backend.core.board import Board
from backend.core.game import *
from backend.core.multiplayer.gameplay import MultiplayerGameplay

type IsRoundOver = bool


class MultiplayerRound:
    def __init__(
        self,
        session_id: uuid.UUID,
        round_number: int,
        board: Board,
        gameplays: list[MultiplayerGameplay],
    ):
        self.session_id = session_id
        self.round_number = round_number
        self.board = board
        self.gameplays = {gameplay.user_id: gameplay for gameplay in gameplays}

        self.start_at = 0
        self.end_at = 0

    def handle_game_action(
        self, action: GameAction, user_id: uuid.UUID
    ) -> ActionResult:
        if not self.start_at or not self.end_at:
            raise RuntimeError("Round has not started yet")

        start_str = datetime.fromtimestamp(self.start_at).strftime("%Y-%m-%d %H:%M:%S")
        end_str = datetime.fromtimestamp(self.end_at).strftime("%Y-%m-%d %H:%M:%S")
        print(
            f"Handling action for round {self.round_number} (started at {start_str}, ends at {end_str})"
        )

        if not self.start_at <= time.time() < self.end_at:
            raise RuntimeError("Round is not active")

        gameplay = self.gameplays[user_id]
        action_result = action.handle(gameplay)

        return action_result

    def is_round_over(self) -> bool:
        return all(gameplay.is_game_over() for gameplay in self.gameplays.values())

    def start(self, start_at, end_at):
        start_str = datetime.fromtimestamp(start_at).strftime("%Y-%m-%d %H:%M:%S")
        end_str = datetime.fromtimestamp(end_at).strftime("%Y-%m-%d %H:%M:%S")

        print(f"Starting round {self.round_number} at {start_str}, ends at {end_str}")
        self.start_at = start_at
        self.end_at = end_at
        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()

    def end(self):
        end_str = datetime.fromtimestamp(self.end_at).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Ending round {self.round_number} at {end_str}")

        for gameplay in self.gameplays.values():
            if not gameplay.is_game_over():
                gameplay.finish_game("loss", loss_cause=LossCause("time_out"))


async def create_multiplayer_round(
    session_id: uuid.UUID,
    round_number: int,
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
        round_number=round_number,
        board=board,
        gameplays=gameplays,
    )
