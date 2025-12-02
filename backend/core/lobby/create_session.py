import uuid
from datetime import timedelta

from backend.core.board import BoardGenerator
from backend.core.lobby.lobby import Lobby
from backend.core.multi.round import Clock, create_multiplayer_round
from backend.core.multi.session import MultiplayerSession


async def create_session(
    id: uuid.UUID,
    lobby: Lobby,
    clock: Clock,
) -> MultiplayerSession:
    game_config = lobby.game_config
    player_ids = [user.id for user in lobby.users]

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
            clock=clock,
        )
        for i in range(game_config.rounds)
    ]

    return MultiplayerSession(
        id=id,
        difficulty_level=dlevel,
        mode=game_config.game_mode,
        max_round_time=game_config.max_round_time,
        player_ids=player_ids,
        clock=clock,
        rounds_number=game_config.rounds,
        rounds=rounds,
    )


__all__ = ["create_session"]
