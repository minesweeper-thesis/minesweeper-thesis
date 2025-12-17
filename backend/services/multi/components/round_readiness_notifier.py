import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from backend.core.lobby.lobby import Lobby
from backend.core.multi import MultiplayerSession
from backend.core.user import User
from backend.services.dto.round import RoundReady, UserNotReady, UserReady

type Sender = Callable[[uuid.UUID, Any], Awaitable[None]]


class RoundReadinessNotifier:
    async def send_user_ready(
        self, sender: Sender, session: MultiplayerSession, user: User
    ):
        next_round_index = session.current_round_index + 1

        for player_id in session.player_ids:
            await sender(player_id, UserReady(user.id, next_round_index))

    async def send_user_ready_in_lobby(self, sender: Sender, lobby: Lobby, user: User):
        for player in lobby.users:
            await sender(player.id, UserReady(user.id, 0))

    async def send_user_not_ready_in_lobby(
        self, sender: Sender, lobby: Lobby, user: User
    ):
        for player in lobby.users:
            await sender(player.id, UserNotReady(user.id, 0))

    async def send_user_not_ready(
        self, sender: Sender, session: MultiplayerSession, user: User
    ):
        next_round_index = session.current_round_index + 1

        for player_id in session.player_ids:
            await sender(player_id, UserNotReady(user.id, next_round_index))

    async def send_round_ready(self, sender: Sender, session: MultiplayerSession):
        next_round_index = session.current_round_index + 1

        for player_id in session.player_ids:
            await sender(
                player_id,
                RoundReady(
                    session.id, next_round_index, session.game_config.difficulty_level
                ),
            )


__all__ = ["RoundReadinessNotifier"]
