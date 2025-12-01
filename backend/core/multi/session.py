import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable

from backend.core.board import BoardGenerator, DifficultyLevel
from backend.core.game import *
from backend.core.multi.config import GameConfig
from backend.core.multi.gameplay import MultiplayerGameplay
from backend.core.multi.round import (
    MultiplayerRound,
    RoundEnd,
    RoundStart,
    create_multiplayer_round,
)


@dataclass
class SessionOver:
    session_id: uuid.UUID


@dataclass
class RoundAwaiting:
    session_id: uuid.UUID
    round: int
    start_at: datetime


@dataclass
class RoundReadyCanceled:
    session_id: uuid.UUID
    round: int


type MultiplayerSessionActionResult = (
    RoundStart | RoundEnd | SessionOver | RoundAwaiting | RoundReadyCanceled | None
)


class MultiplayerSessionAction(ABC):
    @abstractmethod
    def handle(
        self, session: "MultiplayerSession", user_id: uuid.UUID
    ) -> MultiplayerSessionActionResult:
        pass


class ReadyMessage(MultiplayerSessionAction):
    def handle(
        self, session: "MultiplayerSession", user_id: uuid.UUID
    ) -> MultiplayerSessionActionResult:
        return session.set_ready(user_id)


class CancelReadyMessage(MultiplayerSessionAction):
    def handle(
        self, session: "MultiplayerSession", user_id: uuid.UUID
    ) -> MultiplayerSessionActionResult:
        return session.cancel_ready(user_id)


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

        self._ready_players: set[uuid.UUID] = set()

    @property
    def _current_round(self) -> MultiplayerRound:
        if self.current_round_index == -1:
            raise RuntimeError("No round is currently active")
        return self.rounds[self.current_round_index]

    def set_ready(self, user_id: uuid.UUID):
        self._ready_players.add(user_id)

        if self.all_users_ready():
            return RoundAwaiting(
                session_id=self.id,
                round=self._current_round.round_number,
                start_at=self._current_round.start_at,
            )

    def cancel_ready(self, user_id: uuid.UUID):
        self._ready_players.discard(user_id)

    def all_users_ready(self) -> bool:
        return self._ready_players == set(self.player_ids)

    def end_current_round(
        self,
    ) -> tuple[RoundEnd | SessionOver, list[tuple[uuid.UUID, MultiplayerGameplay]]]:
        round_end_data = self._current_round.end()

        over_gameplays_data = []

        for gameplay in round_end_data.time_out_gameplays:
            over_gameplays_data.append((gameplay.user_id, gameplay))

        if self.is_session_over():
            return SessionOver(session_id=self.id), over_gameplays_data

        return round_end_data, over_gameplays_data

    def is_current_round_over(self) -> bool:
        return self._current_round.is_round_over()

    def start_next_round(self, start_at: datetime) -> RoundStart:
        if self.current_round_index != -1:
            if not self._current_round.is_round_over():
                raise RuntimeError("Previous round is not over yet")

        self.current_round_index += 1
        self._ready_players.clear()
        return self._current_round.start(start_at)

    def is_session_over(self) -> bool:
        return self.rounds[-1].is_round_over()

    def get_gameplay_for_user(self, user_id: uuid.UUID) -> MultiplayerGameplay:
        return self._current_round.gameplays[user_id]


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
            round_index=i,
            round_time=timedelta(seconds=game_config.max_round_time),
            board=BoardGenerator(dlevel, gtype, gsettings).generate_board(),
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
