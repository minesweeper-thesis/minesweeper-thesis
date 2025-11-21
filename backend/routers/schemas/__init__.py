from typing import Any

from backend.core.game import *
from backend.core.lobby import *
from backend.routers.schemas.game_schemas import *
from backend.routers.schemas.lobby_schemas import *
from backend.services.lobby_service import GameConfigUpdated, UserConnectionUpdated


def create_response(data: Any) -> str:
    lobby_mapping: dict[Any, type[Response]] = {
        Lobby: InvitationLobbyResponse,
        Invitation: InvitationResponse,
        InvitationAnswer: InvitationAnswerResponse,
        UserConnectionUpdated: UserConnectionStatusResponse,
        GameConfigUpdated: GameConfigUpdatedResponse,
    }

    if type(data) in lobby_mapping:
        return lobby_mapping[type(data)].from_core(data).model_dump_json()

    if isinstance(data, ActionResult):
        return GameActionResponse.from_core(data).model_dump_json()

    raise ValueError(f"Unknown data type: {type(data)}")
