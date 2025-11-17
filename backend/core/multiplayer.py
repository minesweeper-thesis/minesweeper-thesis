import asyncio
import time
import uuid
from abc import abstractmethod
from typing import Any, Awaitable, Callable, Optional

from pydantic import BaseModel

from backend.core.board import Board, BoardGenerator, DifficultyLevel
from backend.core.game import *
from backend.core.lobby import GameConfig
from backend.core.singleplayer import SingleplayerGameplay

ROUND_START_DELAY = 5  # seconds


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

    def _notify_opponents(self):
        my_state = OpponentState(
            revealed_cnt=len(self._gameplay.revealed),
            result=self._gameplay.result,
        )
        self.notify_opponents(my_state)

    def reveal_one(self, x: int, y: int):
        result = self._gameplay.reveal_one(x, y)
        self._notify_opponents()
        return result

    def reveal_many(self, x: int, y: int):
        result = self._gameplay.reveal_many(x, y)
        self._notify_opponents()
        return result

    def flag(self, x: int, y: int) -> FlagResult:
        return self._gameplay.flag(x, y)

    def remove_flag(self, x: int, y: int) -> FlagResult:
        return self._gameplay.remove_flag(x, y)

    def start_game_if_not_started(self):
        self._gameplay.start_game_if_not_started()

    def get_game_state(self) -> GameStateResult:
        return self._gameplay.get_game_state()

    def use_hint(self):
        raise RuntimeError("Hints are not available in multiplayer mode")

    def is_game_over(self) -> bool:
        return self.status == "finished"


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

    def handle_game_action(
        self, action: GameAction, user_id: uuid.UUID
    ) -> ActionResult:
        gameplay = self.gameplays[user_id]
        action_result, _ = action.handle(gameplay)

        return action_result

    def is_round_over(self) -> bool:
        return all(gp.is_game_over() for gp in self.gameplays.values())

    def start(self):
        for gameplay in self.gameplays.values():
            gameplay.start_game_if_not_started()


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
        max_round_time: float,
        player_ids: list[uuid.UUID],
        rounds: list[MultiplayerRound],
    ):
        self.id = id
        self.difficulty_level = difficulty_level
        self.mode = mode
        self.max_round_time = max_round_time
        self.player_ids = player_ids
        self.rounds = rounds
        self.current_round_index = 0

        self.ready_players: set[uuid.UUID] = set()
        self._start_round_task: Optional[asyncio.Task] = None

    async def set_ready(self, user_id: uuid.UUID):
        self.ready_players.add(user_id)

        if set(self.player_ids) == self.ready_players:

            round_start = int(time.time()) + ROUND_START_DELAY
            round_end = round_start + int(self.max_round_time)

            await self._start_round(round_start)

            await self.send_data(
                RoundReady(
                    start_at=round_start,
                    end_at=round_end,
                )
            )

    async def _start_round(self, start_time: int):
        if self._start_round_task is not None:
            self._start_round_task.cancel()

        current_round = self.rounds[self.current_round_index]

        current_time = int(time.time())
        delay = max(0, start_time - current_time)
        await asyncio.sleep(delay)
        current_round.start()

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
    max_round_time: float,
    player_ids: list[uuid.UUID],
    rounds_number: int,
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
        for i in range(rounds_number)
    ]

    return MultiplayerSession(
        id=id,
        difficulty_level=dlevel,
        mode=game_config.game_mode,
        max_round_time=max_round_time,
        player_ids=player_ids,
        rounds=rounds,
    )
