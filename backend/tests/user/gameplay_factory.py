import uuid

from fastapi import BackgroundTasks

from backend.core.board import DifficultyLevel, GenerationSettings
from backend.core.user import User
from backend.db.db import async_session_maker
from backend.lib.board_generator import LocalBoardGenerator
from backend.lib.pending_boards import get_pending_boards_store
from backend.repositories.board_repo import BoardRepository
from backend.repositories.singleplayer_repo import SingleplayerRepository
from backend.services.single.create_gameplay import CreateSingleplayerGameplayUseCase
from backend.services.single.play_single import NewGameSettings, PlaySingleUseCase


async def create_gameplay_via_service(user_id: uuid.UUID) -> uuid.UUID:
    async with async_session_maker() as session:
        board_repo = BoardRepository(session)
        gp_repo = SingleplayerRepository(session)

        board_generator = LocalBoardGenerator(board_repo, BackgroundTasks())

        create = CreateSingleplayerGameplayUseCase(
            board_repo, gp_repo, board_generator, get_pending_boards_store()
        )
        play = PlaySingleUseCase(board_repo, gp_repo, get_pending_boards_store())

        user = User(
            id=user_id,
            nickname="testuser",
            email="testuser@example.com",
            is_online=True,
            settings={},
        )

        difficulty_level = DifficultyLevel(rows=2, columns=2, mine_count=0)
        settings = NewGameSettings(
            board_id=None,
            generator=GenerationSettings(
                type="random", settings=None, difficulty_level=difficulty_level
            ),
            difficulty_level=difficulty_level,
            mode="normal",
        )

        gameplay_id = await create.create_singleplayer_gameplay(user, settings)
        await play.load_gameplay(gameplay_id, timeout=5.0)

        return gameplay_id

        return gameplay_id
