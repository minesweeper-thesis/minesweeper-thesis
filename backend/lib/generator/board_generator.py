import asyncio
import logging
import uuid

from fastapi import BackgroundTasks

from backend import protocols as p
from backend.core.board import Board
from backend.core.board import BoardGenerator as CoreBoardGenerator
from backend.core.board import GenerationSettings
from backend.lib.generator.classifier_provider import get_classifier
from backend.protocols.board_generator_protocol import (
    GenerationID,
    OnBoardGeneratedCallback,
)

logger = logging.getLogger(__name__)


def _create_board(generation_id: GenerationID, settings: GenerationSettings) -> Board:
    logger.debug(f"Board generation {generation_id} in progress")

    classifier = get_classifier(
        settings.difficulty_level,
        settings.settings.classifier if settings.settings else None,
    )

    generator = CoreBoardGenerator(
        settings.difficulty_level,
        settings.type,
        settings.settings,
        classifier,
    )

    board = generator.generate_board()
    logger.info(f"Board generation {generation_id} completed")

    return board


class BackgroundBoardGenerator(p.BoardGenerator):
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    async def generate_board(
        self,
        settings: GenerationSettings,
        on_completed: OnBoardGeneratedCallback,
    ) -> GenerationID:
        generation_id = uuid.uuid4()
        logger.debug(
            f"generate_board(difficulty={settings.difficulty_level}, type={settings.type}), generation_id={generation_id}"
        )

        loop = asyncio.get_running_loop()

        def task():
            board = _create_board(generation_id, settings)
            asyncio.run_coroutine_threadsafe(on_completed(generation_id, board), loop)

        self.background_tasks.add_task(task)

        return generation_id


class AsyncBoardGenerator(p.BoardGenerator):
    def __init__(self):
        pass

    async def generate_board(
        self,
        settings: GenerationSettings,
        on_completed: OnBoardGeneratedCallback,
    ) -> GenerationID:
        generation_id = uuid.uuid4()
        logger.debug(
            f"generate_board(difficulty={settings.difficulty_level}, type={settings.type}), generation_id={generation_id}"
        )

        async def task():
            board = await asyncio.to_thread(_create_board, generation_id, settings)
            await on_completed(generation_id, board)

        asyncio.create_task(task())

        return generation_id
