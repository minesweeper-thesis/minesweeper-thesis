from typing import Any

from backend.core.game import *
from backend.core.lobby import *
from backend.routers.schemas.game_schemas import *
from backend.routers.schemas.lobby_schemas import *
from backend.services.lobby_service import GameConfigUpdated, UserConnectionUpdated


def create_response(data: Any) -> str:
    lobby_mapping = {
        Lobby: InvitationLobbyResponse,
        Invitation: InvitationResponse,
        InvitationAnswer: InvitationAnswerResponse,
        UserConnectionUpdated: UserConnectionStatusResponse,
        GameConfigUpdated: GameConfigUpdatedResponse,
    }

    game_mapping = {
        RevealResult: GameActionResponse,
        FlagResult: GameActionResponse,
        HintResult: GameActionResponse,
        GameOverResult: GameActionResponse,
    }

    mapping = {**lobby_mapping, **game_mapping}

    return mapping[type(data)].create(data).model_dump_json(exclude_none=True)
