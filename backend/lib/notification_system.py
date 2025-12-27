import logging
import uuid
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

from backend.core.game import GameState
from backend.core.game.game_actions import *
from backend.core.lobby import *
from backend.core.multi import *
from backend.core.user import FriendRequest
from backend.core.user.chat import UserChatMessage
from backend.lib.websockets.websockets_registry import WebsocketsRegistry
from backend.protocols import NotificationSystem
from backend.schemas import Response
from backend.schemas.game import *
from backend.schemas.lobby import *
from backend.schemas.lobby import UserOnlineUpdatedResponse
from backend.schemas.user import FriendRequestResponse, UserChatMessageResponse
from backend.services.dto import *
from backend.services.dto.lobby import SessionState, UserCurrentLobby, UserOnlineUpdated


class WSNotificationSystem(NotificationSystem):
    def __init__(self):
        self._notifications_websockets = WebsocketsRegistry()

    def connect_user(self, user_id: uuid.UUID, websocket: WebSocket):
        logger.debug(f"connect_user(user_id={user_id})")
        self._notifications_websockets.add(user_id, websocket)
        logger.info(f"User {user_id} connected to notification system")

    def disconnect_user(self, user_id: uuid.UUID):
        logger.debug(f"disconnect_user(user_id={user_id})")
        self._notifications_websockets.remove(user_id)
        logger.info(f"User {user_id} disconnected from notification system")

    async def notify(self, receiver_id: uuid.UUID, data):
        logger.debug(
            f"notify(receiver_id={receiver_id}, data_type={type(data).__name__})"
        )
        if self._notifications_websockets.is_connected(receiver_id):
            websocket = self._notifications_websockets.get(receiver_id)
            logger.debug(
                f"Sending notification to {receiver_id}: {type(data).__name__}"
            )
            await websocket.send_text(create_notification(data))
        else:
            logger.debug(
                f"User {receiver_id} not connected, skipping notification: {type(data).__name__}"
            )


_notification_system = WSNotificationSystem()


def get_notification_system():
    return _notification_system


def create_notification(data: Any) -> str:
    mapping: dict[type, type["Response"]] = {
        Invitation: InvitationResponse,
        FriendRequest: FriendRequestResponse,
        KickedFromLobby: KickedResponse,
        UserChatMessage: UserChatMessageResponse,
        UserCurrentLobby: CurrentLobbyResponse,
    }

    if type(data) not in mapping:
        raise ValueError(f"Unsupported response type: {type(data)}")

    return mapping[type(data)].create(data, include_ws_type=True)


type Notifiable = RoundStart | RoundEnd | RoundCountdown | SessionOver | GameActionResult | GameState | UserReady


def create_game_notification(data: Notifiable) -> str:

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
        InvitationAnswer: InvitationAnswerResponse,
        LobbyChatMessage: LobbyChatMessageResponse,
        UserOnlineUpdated: UserOnlineUpdatedResponse,
        UserConnectionUpdated: UserConnectionStatusResponse,
        GameConfigUpdated: GameConfigUpdatedResponse,
        SessionState: SessionStateResponse,
    }

    if type(data) not in mapping:
        raise ValueError(f"Unsupported response type: {type(data)}")

    return mapping[type(data)].create(data, include_ws_type=True)
