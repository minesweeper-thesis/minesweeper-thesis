import uuid
from abc import abstractmethod
from typing import Any, Awaitable, Callable

from backend.core.board import BoardGenerator, DifficultyLevel
from backend.core.game import *
from backend.core.lobby import GameConfig
from backend.core.multi.round import (
    MultiplayerRound,
    RoundEnd,
    RoundStart,
    create_multiplayer_round,
)


class MultiplayerSessionMessage(ABC):
    @abstractmethod
    def handle(self, session: "MultiplayerSession", user_id: uuid.UUID):
        pass


class ReadyMessage(MultiplayerSessionMessage):
    def handle(self, session: "MultiplayerSession", user_id: uuid.UUID):
        _ = session.set_ready(user_id)


class CancelReadyMessage(MultiplayerSessionMessage):
    def handle(self, session: "MultiplayerSession", user_id: uuid.UUID):
        session.set_not_ready(user_id)


@dataclass
class SessionOver:
    session_id: uuid.UUID


@dataclass
class GameReady:
    session_id: uuid.UUID
    round: int
    start_at: int


type MultiplayerResult = GameActionResult | RoundStart | RoundEnd | SessionOver | GameReady


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

    @property
    def current_round(self) -> MultiplayerRound:
        if self.current_round_index == -1:
            raise RuntimeError("No round is currently active")
        return self.rounds[self.current_round_index]

    def end_current_round(
        self,
    ) -> tuple[RoundEnd | SessionOver, list[tuple[uuid.UUID, GameOverResult]]]:
        if self.current_round_index == -1:
            raise RuntimeError("No round is currently active")

        current_round = self.rounds[self.current_round_index]
        round_end_data = current_round.end()

        over_gameplays_data = []

        gameplays = self.rounds[self.current_round_index].gameplays
        for user_id, gameplay in gameplays.items():
            if gameplay.loss_cause == LossCause("time_out"):
                game_over_data = GameOverResult(
                    result="loss",
                    full_board=gameplay._gameplay.grid.grid,
                    elapsed_time=gameplay.time,
                    loss_cause=gameplay.loss_cause,
                )
                over_gameplays_data.append((user_id, game_over_data))

        if self.is_session_over():
            return SessionOver(session_id=self.id), over_gameplays_data

        return round_end_data, over_gameplays_data

    def start_next_round(self, start_at: int, end_at: int) -> RoundStart:
        if self.current_round_index != -1:
            previous_round = self.rounds[self.current_round_index]
            if not previous_round.is_round_over():
                raise RuntimeError("Previous round is not over yet")

        self.current_round_index += 1
        current_round = self.rounds[self.current_round_index]
        data = current_round.start(start_at, end_at)
        self.ready_players.clear()
        return data

    def set_not_ready(self, user_id: uuid.UUID):
        self.ready_players.discard(user_id)

    def is_session_over(self) -> bool:
        return self.rounds[-1].is_round_over()

    def handle_game_action(
        self, action: GameAction, user_id: uuid.UUID
    ) -> GameActionResult:
        current_round = self.rounds[self.current_round_index]
        action_result = current_round.handle_game_action(action, user_id)

        return action_result

    def start_countdown(self, start_at: int) -> GameReady:
        return GameReady(
            session_id=self.id, round=self.current_round_index + 1, start_at=start_at
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
