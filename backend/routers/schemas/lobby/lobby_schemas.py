import uuid
from typing import Literal, Optional, Self

from pydantic import BaseModel

from backend.core.board import DifficultyLevel
from backend.core.game import GameMode
from backend.core.lobby import *
from backend.core.multi import *
from backend.routers.schemas import Response
from backend.routers.schemas.game.single_schemas import GeneratorSchema
from backend.routers.schemas.lobby import ChatMessageResponse
from backend.routers.schemas.user import UserResponse


class GameConfigResponse(BaseModel):
    rounds: int
    max_round_time: int
    difficulty_level: DifficultyLevel
    game_mode: GameMode
    generator: GeneratorSchema

    @classmethod
    def build(cls, config: GameConfig) -> Self:
        return cls(
            rounds=config.rounds,
            max_round_time=config.max_round_time,
            difficulty_level=config.difficulty_level,
            game_mode=config.game_mode,
            generator=GeneratorSchema.from_dto(config.generator),
        )


class LobbyResponse(BaseModel):
    id: uuid.UUID
    host: UserResponse
    users: list[UserResponse]
    game_config: GameConfigResponse
    messages: list[ChatMessageResponse] = []

    @classmethod
    def build(cls, lobby: Lobby, messages: list[LobbyChatMessage] = []) -> Self:
        return cls(
            id=lobby.id,
            host=UserResponse.build(lobby.host),
            users=[UserResponse.build(user) for user in lobby.users],
            game_config=GameConfigResponse.build(lobby.game_config),
            messages=[ChatMessageResponse.build(message) for message in messages],
        )


class DifficultyLevelRequest(BaseModel):
    rows: int
    columns: int
    mine_count: int


class UpdateGameConfigRequest(BaseModel):
    rounds: int
    max_round_time: int
    difficulty_level: DifficultyLevelRequest
    game_mode: GameMode
    generator: GeneratorSchema

    def to_dto(self) -> GameConfig:
        return GameConfig(
            rounds=self.rounds,
            max_round_time=self.max_round_time,
            difficulty_level=DifficultyLevel(
                rows=self.difficulty_level.rows,
                columns=self.difficulty_level.columns,
                mine_count=self.difficulty_level.mine_count,
            ),
            game_mode=self.game_mode,
            generator=self.generator.to_dto(),
        )


class GameConfigUpdatedResponse(Response):
    ws_type: Literal["game_config_updated"] = "game_config_updated"
    lobby_id: uuid.UUID
    game_config: GameConfigResponse

    @classmethod
    def build(cls, data: GameConfigUpdated) -> Self:
        return cls(
            lobby_id=data.lobby_id,
            game_config=GameConfigResponse.build(data.game_config),
        )


class UserConnectionStatusResponse(Response):
    ws_type: Literal["user_connection_status"] = "user_connection_status"
    lobby_id: uuid.UUID
    user: UserResponse
    status: Literal["connected", "disconnected"]

    @classmethod
    def build(cls, data: UserConnectionUpdated) -> Self:
        return cls(
            lobby_id=data.lobby_id,
            user=UserResponse.build(data.user),
            status=data.status,
        )


class CurrentLobbyResponse(Response):
    ws_type: Literal["current_lobby"] = "current_lobby"
    lobby: Optional[LobbyResponse]

    @classmethod
    def build(cls, lobby: Optional[Lobby]) -> Self:
        return cls(
            lobby=LobbyResponse.build(lobby) if lobby else None,
        )


class KickUserRequest(BaseModel):
    user_id: uuid.UUID


class KickedResponse(Response):
    ws_type: Literal["current_lobby"] = "current_lobby"
    lobby: None = None
    reason: Literal["kicked"] = "kicked"

    @classmethod
    def build(cls, lobby_id: uuid.UUID) -> Self:
        return cls(lobby=None)


__all__ = [
    "UpdateGameConfigRequest",
    "LobbyResponse",
    "GameConfigUpdatedResponse",
    "UserConnectionStatusResponse",
    "CurrentLobbyResponse",
    "GameConfigUpdatedResponse",
    "KickUserRequest",
    "KickedResponse",
]
