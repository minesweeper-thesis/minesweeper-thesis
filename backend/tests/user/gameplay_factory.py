import uuid

from backend.core.board import DifficultyLevel, GenerationSettings
from backend.infra.board_generator import LocalBoardGenerator
from backend.infra.pending_boards import get_pending_boards_store
from backend.services.single.create_gameplay import CreateSingleplayerGameplayUseCase


async def create_gameplay_via_service(user_id) -> uuid.UUID:
    # import dependencies lazily to avoid import-time DB/DI side-effects
    from fastapi import BackgroundTasks

    from backend.db.db import async_session_maker
    from backend.repositories.board_repo import BoardRepository
    from backend.repositories.singleplayer_repo import SingleplayerRepository
    from backend.services.single.singleplayer_service import (
        NewGameSettings,
        SingleplayerGameplayUseCase,
    )

    async with async_session_maker() as session:
        board_repo = BoardRepository(session)
        gp_repo = SingleplayerRepository(session)

        board_generator = LocalBoardGenerator(board_repo, BackgroundTasks())

        create = CreateSingleplayerGameplayUseCase(
            board_repo, gp_repo, board_generator, get_pending_boards_store()
        )
        play = SingleplayerGameplayUseCase(
            board_repo, gp_repo, get_pending_boards_store()
        )

        if isinstance(user_id, str):
            user_obj = type("U", (), {"id": uuid.UUID(user_id)})()
        else:
            user_obj = type("U", (), {"id": user_id})()

        difficulty_level = DifficultyLevel(rows=2, columns=2, mine_count=0)
        settings = NewGameSettings(
            board_id=None,
            generator=GenerationSettings(
                type="random", settings=None, difficulty_level=difficulty_level
            ),
            difficulty_level=difficulty_level,
            mode="normal",
        )

        gameplay_id = await create.create_singleplayer_gameplay(user_obj, settings)

        await play.load_gameplay(gameplay_id, timeout=5.0)

        return gameplay_id
