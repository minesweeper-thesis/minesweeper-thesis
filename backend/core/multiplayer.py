import time
import uuid
from abc import abstractmethod
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from pydantic import BaseModel

from backend.core.board import Board, BoardGenerator, DifficultyLevel
from backend.core.game import *
from backend.core.lobby import GameConfig
from backend.core.singleplayer import SingleplayerGameplay

ROUND_START_DELAY = 10  # seconds


class OpponentState(BaseModel):
    revealed_cnt: int
    result: Optional[GameResult]


type Notifier = Callable[[OpponentState], None]
type IsSessionOver = bool


class MultiplayerGameplay(Gameplay):
    def __init__(
        self,
        user_id: uuid.UUID,
        board: Board,
        mode: GameMode,
        notify_opponents: Notifier,
        revealed_cells: list[tuple[int, int]] = [],
        status: GameStatus = "not_started",
        result: Optional[GameResult] = None,
        elapsed_time: float = 0,
    ):
        self.user_id = user_id
        self.notify_opponents = notify_opponents

        self._gameplay = SingleplayerGameplay(
            id=uuid.uuid4(),
            board=board,
            revealed_cells=revealed_cells,
            status=status,
            result=result,
            used_hints=False,
            elapsed_time=elapsed_time,
            mode=mode,
        )

    @property
    def time(self) -> float:
        return self._gameplay.elapsed_time

    @property
    def status(self) -> GameStatus:
        return self._gameplay.status

    @property
    def result(self) -> Optional[GameResult]:
        return self._gameplay.result

    @property
    def revealed_cells(self) -> list[tuple[int, int]]:
        return self._gameplay.get_revealed_cells()

    @property
    def board(self) -> Board:
        return self._gameplay.board

    @property
    def mode(self) -> GameMode:
        return self._gameplay.game_mode

    @property
    def loss_cause(self) -> Optional[LossCause]:
        return self._gameplay.loss_cause

    def _notify_opponents(self):
        my_state = OpponentState(
            revealed_cnt=len(self._gameplay.revealed),
            result=self._gameplay.result,
        )
        self.notify_opponents(my_state)

    def reveal_one(self, x: int, y: int):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        result = self._gameplay.reveal_one(x, y)
        self._notify_opponents()
        return result

    def reveal_many(self, x: int, y: int):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        result = self._gameplay.reveal_many(x, y)
        self._notify_opponents()
        return result

    def flag(self, x: int, y: int) -> FlagResult:
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.flag(x, y)

    def remove_flag(self, x: int, y: int) -> FlagResult:
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        return self._gameplay.remove_flag(x, y)

    def start_game_if_not_started(self):
        self._gameplay.start_game_if_not_started()

    def get_game_state(self) -> GameStateResult:
        return self._gameplay.get_game_state()

    def use_hint(self):
        raise RuntimeError("Hints are not available in multiplayer mode")

    def is_game_over(self) -> bool:
        return self.status == "finished"

    def finish_game(self, result: GameResult, loss_cause: Optional[LossCause] = None):
        if self.status != "in_progress":
            raise RuntimeError("Game is not in progress")

        self._gameplay.finish_game(result, loss_cause)


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


class MultiplayerSessionMessage(ABC):
    @abstractmethod
    def handle(self, session: "MultiplayerSession", user_id: uuid.UUID):
        pass


class ReadyMessage(MultiplayerSessionMessage):
    def handle(self, session: "MultiplayerSession", user_id: uuid.UUID):
        _ = session.set_ready(user_id)


class NotReadyMessage(MultiplayerSessionMessage):
    def handle(self, session: "MultiplayerSession", user_id: uuid.UUID):
        session.set_not_ready(user_id)


@dataclass
class RoundReady:
    start_at: int
    end_at: int


class MultiplayerSession:
    send_data: Callable[[Any], Awaitable[None]]

    def __init__(
        self,
        id: uuid.UUID,
        difficulty_level: DifficultyLevel,
        mode: GameMode,
        max_round_time: int,
        player_ids: list[uuid.UUID],
        rounds: list[MultiplayerRound],
    ):
        self.id = id
        self.difficulty_level = difficulty_level
        self.mode = mode
        self.max_round_time = max_round_time
        self.player_ids = player_ids
        self.rounds = rounds
        self.current_round_index = -1

        self.ready_players: set[uuid.UUID] = set()

    def set_ready(self, user_id: uuid.UUID):
        self.ready_players.add(user_id)

    def all_users_ready(self) -> bool:
        return set(self.player_ids) == self.ready_players

    def end_current_round(self):
        if self.current_round_index == -1:
            raise RuntimeError("No round is currently active")

        current_round = self.rounds[self.current_round_index]
        current_round.end()

    def start_next_round(self, start_at: int, end_at: int):
        if self.current_round_index != -1:
            previous_round = self.rounds[self.current_round_index]
            if not previous_round.is_round_over():
                raise RuntimeError("Previous round is not over yet")

        self.current_round_index += 1
        current_round = self.rounds[self.current_round_index]
        current_round.start(start_at, end_at)
        self.ready_players.clear()

    def set_not_ready(self, user_id: uuid.UUID):
        self.ready_players.discard(user_id)

    def is_session_over(self) -> bool:
        return self.rounds[-1].is_round_over()

    def handle_game_action(
        self, action: GameAction, user_id: uuid.UUID
    ) -> ActionResult:
        current_round = self.rounds[self.current_round_index]
        action_result = current_round.handle_game_action(action, user_id)

        return action_result


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


async def create_multiplayer_session(
    id: uuid.UUID,
    game_config: GameConfig,
    player_ids: list[uuid.UUID],
) -> MultiplayerSession:
    dlevel, gtype, gsettings = (
        game_config.difficulty_level,
        game_config.generator_type,
        game_config.generator_settings,
    )

    rounds = [
        await create_multiplayer_round(
            session_id=id,
            round_number=i + 1,
            board=await BoardGenerator(dlevel, gtype, gsettings).generate_board(),
            player_ids=player_ids,
            mode=game_config.game_mode,
        )
        for i in range(game_config.rounds)
    ]

    return MultiplayerSession(
        id=id,
        difficulty_level=dlevel,
        mode=game_config.game_mode,
        max_round_time=game_config.max_round_time,
        player_ids=player_ids,
        rounds=rounds,
    )
