import asyncio
import itertools
import logging

from backend.core.board import DifficultyLevel, GenerationSettings, GeneratorParams
from backend.core.board.generator import BoardGenerator
from backend.db.db import async_session_maker
from backend.lib.generator.classifier_provider import get_classifier
from backend.repositories.board_repo import BoardRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.jobs.background_generator")

CLASSIFIERS = "lightgbm", "catboost", "gaussiannb", "xgboost"

HEURISTICS = "GA", "PSO", "SA", "naive"

HEURISTIC_ARGS = {
    "GA": (50, 50, 25, 0.5),
    "PSO": (50, 50, 0.65, 1.75, 1.75),
    "SA": (50, 25, 10.0, 0.5),
    "naive": (500,),
}

DIFFICULTIES = (
    DifficultyLevel.easy(),
    DifficultyLevel.medium(),
    DifficultyLevel.hard(),
)


async def background_board_generator():
    logger.info("Starting background board generator")

    to_generate = (
        GenerationSettings(
            type="ml",
            difficulty_level=difficulty,
            settings=GeneratorParams(classifier, heuristic, HEURISTIC_ARGS[heuristic]),
        )
        for heuristic, classifier, difficulty in itertools.product(
            HEURISTICS, CLASSIFIERS, DIFFICULTIES
        )
    )

    for generation_settings in itertools.cycle(to_generate):
        try:
            logger.debug(f"Generating board: {generation_settings}")
            assert generation_settings.settings is not None

            generator = BoardGenerator(
                generation_settings.difficulty_level,
                "ml",
                settings=generation_settings.settings,
                classifier=get_classifier(
                    generation_settings.difficulty_level,
                    generation_settings.settings.classifier,
                    generation_settings.settings.heuristic,
                ),
            )
            board = generator.generate_board()

            async with async_session_maker() as session:
                board_repo = BoardRepository(session)
                await board_repo.add_board(board)

            logger.info(f"Successfully generated and saved board {board.id}")

            await asyncio.sleep(1)

        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(background_board_generator())
