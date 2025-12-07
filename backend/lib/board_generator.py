import asyncio
import uuid

from fastapi import BackgroundTasks

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
        generation_id = uuid.uuid4()
        _generation_statuses[generation_id] = "pending"

        def task():
            generator = CoreBoardGenerator(
                settings.difficulty_level,
                settings.type,
                settings.settings,
            )
            _generation_statuses[generation_id] = "in_progress"
            board = generator.generate_board()
            _generation_statuses[generation_id] = "completed"

            asyncio.run(on_completed(generation_id, board))  # type: ignore

        self.background_tasks.add_task(task)

        return generation_id

    async def get_generation_status(
        self, generation_id: GenerationID
    ) -> GenerationStatus:
        try:
            return _generation_statuses[generation_id]
        except KeyError:
            raise GenerationNotFound()
