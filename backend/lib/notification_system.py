import uuid
from typing import Any

from backend.core.game import GameState
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import FriendRequest
from backend.lib.websockets.connections_manager import connections_manager
from backend.routers.schemas import Response
from backend.routers.schemas.game import *
from backend.routers.schemas.lobby import *
from backend.routers.schemas.user import FriendRequestResponse
from backend.services.single.game_actions import *


class NotificationSystem:
    async def notify(self, receiver_id: uuid.UUID, data):
        if connections_manager.is_user_online(receiver_id):
            websocket = connections_manager.get(receiver_id)
            await websocket.send_text(create_notification(data))


def get_notification_system() -> NotificationSystem:
    return NotificationSystem()


def create_notification(data: Any) -> str:
    mapping: dict[type, type[Response]] = {
        GameConfigUpdated: GameConfigUpdatedResponse,
        Invitation: InvitationResponse,
        InvitationAnswer: InvitationAnswerResponse,
        UserConnectionUpdated: UserConnectionStatusResponse,
        RoundStartAwaiting: GameReadyResponse,
        ChatMessage: ChatMessageResponse,
        FriendRequest: FriendRequestResponse,
    }

    if type(data) not in mapping:
        raise ValueError("Unsupported response type")

    return mapping[type(data)].create(data, include_ws_type=True)


type Notifiable = RoundStart | RoundEnd | RoundStartAwaiting | RoundStartCanceled | SessionOver | GameActionResult | GameState


def create_game_notification(
    data: Notifiable,
) -> str:
    mapping: dict[type[Notifiable], type[Response]] = {
        RoundStartAwaiting: GameReadyResponse,
        SessionOver: SessionOverResponse,
        RoundStart: RoundStartResponse,
        RoundEnd: RoundEndResponse,
        RevealResult: RevealResponse,
        GameOverResult: GameOverResponse,
        GameState: GameStateResponse,
        FlagResult: FlagResponse,
        RemoveFlagResult: RemoveFlagResponse,
        HintResult: HintResponse,
    }

    if type(data) not in mapping:
        raise RuntimeError("Unsupported response type")

    return mapping[type(data)].create(data, include_ws_type=True)
