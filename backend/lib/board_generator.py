import asyncio
import uuid
from typing import Annotated

from fastapi import BackgroundTasks, Depends

from backend import repositories
from backend.core.board import BoardGenerator as CoreBoardGenerator
from backend.core.board import GenerationSettings
from backend.protocols.board_generator_protocol import *
from backend.repositories.exceptions import BoardNotFound

_generation_statuses: dict[uuid.UUID, GenerationStatus] = {}


class LocalBoardGenerator(BoardGenerator):
    def __init__(
        self,
        board_repo: Annotated[repositories.BoardRepository, Depends()],
        background_tasks: BackgroundTasks,
    ):
        self.board_repo = board_repo
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

            try:
                existing_board = asyncio.run(
                    self.board_repo.get_board(board.difficulty_level, board._minefields)
                )
                board = existing_board
            except BoardNotFound:
                asyncio.run(self.board_repo.add_board(board))

            asyncio.run(on_completed(generation_id, board.id))  # type: ignore

        self.background_tasks.add_task(task)

        return generation_id

    async def get_generation_status(
        self, generation_id: GenerationID
    ) -> GenerationStatus:
        try:
            return _generation_statuses[generation_id]
        except KeyError:
            raise GenerationNotFound()
