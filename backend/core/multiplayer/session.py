import uuid
from abc import abstractmethod
from typing import Any, Awaitable, Callable

from backend.core.board import BoardGenerator, DifficultyLevel
from backend.core.game import *
from backend.core.lobby import GameConfig
from backend.core.multiplayer.round import MultiplayerRound, create_multiplayer_round


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


type IsSessionOver = bool


@dataclass
class GameReady:
    session_id: uuid.UUID
    round: int
    start_at: int


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
