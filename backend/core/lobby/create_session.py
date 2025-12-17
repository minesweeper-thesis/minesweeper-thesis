import uuid

from backend.core.lobby.lobby import Lobby
from backend.core.multi.session import MultiplayerSession


async def create_session(id: uuid.UUID, lobby: Lobby) -> MultiplayerSession:
    game_config = lobby.game_config
    player_ids = [user.id for user in lobby.users]

    return MultiplayerSession(
        id=id,
        lobby_id=lobby.id,
        difficulty_level=game_config.difficulty_level,
        game_config=game_config,
        player_ids=player_ids,
        rounds_number=game_config.rounds,
    )


__all__ = ["create_session"]
