import asyncio
import uuid

from backend.core.board import DifficultyLevel, GenerationSettings


async def create_gameplay_via_service(user_id) -> uuid.UUID:
    # import dependencies lazily to avoid import-time DB/DI side-effects
    from fastapi import BackgroundTasks

    from backend.db.db import async_session_maker
    from backend.repositories.board_repo import BoardRepository
    from backend.repositories.singleplayer_repo import SingleplayerRepository
    from backend.services.singleplayer_service import (
        NewGameSettings,
        SingleplayerService,
    )

    async with async_session_maker() as session:
        board_repo = BoardRepository(session)
        gp_repo = SingleplayerRepository(session)

        # run generation synchronously in test to avoid background scheduling
        class ImmediateBG:
            def add_task(self, func, *a, **kw):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    # No running loop: call directly (sync test case)
                    return func(*a, **kw)
                else:
                    # We're inside an event loop (async test). Run the task
                    # in a separate thread so that any inner `asyncio.run()`
                    # calls inside `func` execute in a fresh loop without
                    # conflicting with the running loop.
                    from functools import partial

                    return loop.run_in_executor(None, partial(func, *a, **kw))

        svc = SingleplayerService(board_repo, gp_repo, ImmediateBG())

        if isinstance(user_id, str):
            user_obj = type("U", (), {"id": uuid.UUID(user_id)})()
        else:
            user_obj = type("U", (), {"id": user_id})()

        settings = NewGameSettings(
            board_id=None,
            generator=GenerationSettings(type="random", settings=None),
            difficulty_level=DifficultyLevel(rows=2, columns=2, mine_count=0),
            mode="normal",
        )

        gameplay_id = await svc.create_singleplayer_gameplay(user_obj, settings)

        # minimal transport to satisfy load_gameplay
        class DummyTransport:
            async def receive_action(self):
                await asyncio.sleep(0)
                return None

            async def send(self, result):
                return None

            async def close(self):
                return None

        await svc.load_gameplay(gameplay_id, DummyTransport(), timeout=5.0)

        return gameplay_id
