import asyncio
import logging
import uuid

from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

from backend.core.board import BoardGenerator as CoreBoardGenerator
from backend.core.board import GenerationSettings
from backend.protocols.board_generator_protocol import *

_generation_statuses: dict[uuid.UUID, GenerationStatus] = {}


class LocalBoardGenerator(BoardGenerator):
    def __init__(self, background_tasks: BackgroundTasks):
        self.background_tasks = background_tasks

    async def generate_board(
        self,
        settings: GenerationSettings,
        on_completed: OnBoardGeneratedCallback,
    ) -> GenerationID:
        logger.debug(
            f"generate_board(difficulty={settings.difficulty_level}, type={settings.type})"
        )
        generation_id = uuid.uuid4()
        _generation_statuses[generation_id] = "pending"
        logger.info(
            f"Starting board generation {generation_id} with settings: {settings.difficulty_level}"
        )

        loop = asyncio.get_running_loop()

        def task():
            generator = CoreBoardGenerator(
                settings.difficulty_level,
                settings.type,
                settings.settings,
            )
            _generation_statuses[generation_id] = "in_progress"
            logger.debug(f"Board generation {generation_id} in progress")
            board = generator.generate_board()
            _generation_statuses[generation_id] = "completed"
            logger.info(f"Board generation {generation_id} completed")
            asyncio.run_coroutine_threadsafe(on_completed(generation_id, board), loop)

        self.background_tasks.add_task(task)

        return generation_id

    async def get_generation_status(
        self, generation_id: GenerationID
    ) -> GenerationStatus:
        logger.debug(f"get_generation_status(generation_id={generation_id})")
        try:
            return _generation_statuses[generation_id]
        except KeyError:
            raise GenerationNotFound()
