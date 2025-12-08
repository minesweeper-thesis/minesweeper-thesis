from datetime import datetime
from typing import Callable

from backend.core.lobby.lobby import Lobby
from backend.core.multi import MultiplayerSession
from backend.core.user import User
from backend.services.dto.round import RoundReady, UserNotReady, UserReady
from backend.services.multi.constants import COUNTDOWN_DELAY, START_DELAY


def calc_round_start_times():
    countdown_to = datetime.now() + COUNTDOWN_DELAY
    start_at = countdown_to + START_DELAY
    return countdown_to, start_at


async def send_user_ready(sender: Callable, session: MultiplayerSession, user: User):
    next_round_index = session.current_round_index + 1

    for player_id in session.player_ids:
        await sender(player_id, UserReady(user.id, next_round_index))


async def send_user_ready_in_lobby(sender: Callable, lobby: Lobby, user: User):
    for player in lobby.users:
        await sender(player.id, UserReady(user.id, 0))


async def send_user_not_ready_in_lobby(sender: Callable, lobby: Lobby, user: User):
    for player in lobby.users:
        await sender(player.id, UserNotReady(user.id, 0))


async def send_user_not_ready(
    sender: Callable, session: MultiplayerSession, user: User
):
    next_round_index = session.current_round_index + 1

    for player_id in session.player_ids:
        await sender(player_id, UserNotReady(user.id, next_round_index))


async def send_round_ready(sender: Callable, session: MultiplayerSession):
    next_round_index = session.current_round_index + 1

    for player_id in session.player_ids:
        await sender(
            player_id,
            RoundReady(
                session.id, next_round_index, session.game_config.difficulty_level
            ),
        )
