import uuid
from typing import Any

from fastapi import WebSocket

from backend.core.game import GameState
from backend.core.game.game_actions import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import FriendRequest
from backend.core.user.chat import UserChatMessage
from backend.lib.websockets.websockets_registry import WebsocketsRegistry
from backend.protocols import NotificationSystem
from backend.routers.schemas import Response
from backend.routers.schemas.game import *
from backend.routers.schemas.lobby import *
from backend.routers.schemas.user import FriendRequestResponse, UserChatMessageResponse
from backend.services.dto import *


class WSNotificationSystem(NotificationSystem):
    def __init__(self):
        self._notifications_websockets = WebsocketsRegistry()

    def connect_user(self, user_id: uuid.UUID, websocket: WebSocket):
        self._notifications_websockets.add(user_id, websocket)

    def disconnect_user(self, user_id: uuid.UUID):
        self._notifications_websockets.remove(user_id)

    async def notify(self, receiver_id: uuid.UUID, data):
        if self._notifications_websockets.is_connected(receiver_id):
            websocket = self._notifications_websockets.get(receiver_id)
            await websocket.send_text(create_notification(data))


_notification_system = WSNotificationSystem()


def get_notification_system():
    return _notification_system


def create_notification(data: Any) -> str:
    mapping: dict[type, type["Response"]] = {
        GameConfigUpdated: GameConfigUpdatedResponse,
        Invitation: InvitationResponse,
        InvitationAnswer: InvitationAnswerResponse,
        UserConnectionUpdated: UserConnectionStatusResponse,
        RoundReady: RoundReadyResponse,
        RoundCountdown: RoundCountdownResponse,
        UserReady: UserReadyResponse,
        LobbyChatMessage: LobbyChatMessageResponse,
        FriendRequest: FriendRequestResponse,
        UserNotReady: UserNotReadyResponse,
        KickedFromLobby: KickedResponse,
        UserChatMessage: UserChatMessageResponse,
    }

    if type(data) not in mapping:
        raise ValueError(f"Unsupported response type: {type(data)}")

    return mapping[type(data)].create(data, include_ws_type=True)


type Notifiable = RoundStart | RoundEnd | RoundCountdown | SessionOver | GameActionResult | GameState | UserReady


def create_game_notification(
    data: Notifiable,
) -> str:

    mapping: dict[type[Any], type[Response]] = {
        RoundReady: RoundReadyResponse,
        RoundCountdown: RoundCountdownResponse,
        SessionOver: SessionOverResponse,
        RoundStart: RoundStartResponse,
        RoundEnd: RoundEndResponse,
        RevealResult: RevealResponse,
        GameOverResult: GameOverResponse,
        GameState: GameStateResponse,
        FlagResult: FlagResponse,
        RemoveFlagResult: RemoveFlagResponse,
        HintResult: HintResponse,
        UserReady: UserReadyResponse,
        UserNotReady: UserNotReadyResponse,
        ScoreUpdate: ScoreUpdateResponse,
    }

    if type(data) not in mapping:
        raise RuntimeError(f"Unsupported response type: {type(data)}")

    return mapping[type(data)].create(data, include_ws_type=True)
