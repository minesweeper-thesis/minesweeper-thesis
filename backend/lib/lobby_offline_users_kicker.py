import asyncio
import logging
import uuid
from contextlib import suppress

from backend.core.lobby.lobby import UserNotInLobby
from backend.db import async_session_maker
from backend.lib.notification_system import get_notification_system
from backend.lib.redis_client import get_redis_client
from backend.lib.session_lock import SessionLock
from backend.repositories import (
    RedisLobbyRepository,
    RedisMultiplayerRepository,
    UserRepository,
)
from backend.services.exceptions import LobbyNotExists
from backend.services.lobby.lobby_service import LobbyService

logger = logging.getLogger(__name__)


class LobbyOfflineUsersKicker:
    def __init__(self) -> None:
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()
        self.prefix = "lobby_kick:"

    async def start(self) -> None:
        if self._task is not None:
            return

        logger.debug("LobbyOfflineUsersKicker.start() called")
        self._task = asyncio.create_task(self._run())
        logger.info("LobbyOfflineUsersKicker started")

    async def stop(self) -> None:
        if self._task is None:
            return

        self._stopped.set()
        self._task.cancel()
        with suppress(asyncio.CancelledError):
            await self._task
        self._task = None
        self._stopped = asyncio.Event()
        logger.info("LobbyOfflineUsersKicker stopped")

    async def _run(self) -> None:
        logger.debug("LobbyOfflineUsersKicker _run() loop starting")
        redis_client = await get_redis_client()
        pubsub = redis_client.pubsub()

        await pubsub.psubscribe("__keyevent@*__:expired")
        logger.info(
            "LobbyOfflineUsersKicker subscribed to Redis key expiration events pattern=%s",
            "__keyevent@*__:expired",
        )

        try:
            async for message in pubsub.listen():
                if self._stopped.is_set():
                    logger.debug(
                        "LobbyOfflineUsersKicker stop flag set, breaking listen loop"
                    )
                    break

                if message.get("type") != "pmessage":
                    continue

                key = message.get("data")
                if not key:
                    logger.debug(
                        "Received Redis expiration message without data: %s", message
                    )
                    continue

                key = key.decode("utf-8") if isinstance(key, bytes) else key
                if not isinstance(key, str):
                    logger.debug("Decoded Redis key is not a string, skipping: %r", key)
                    continue

                logger.debug("Received expired Redis key event for key=%s", key)

                if not key.startswith(self.prefix):
                    logger.debug(
                        "Expired Redis key %s does not match kick prefix %s, skipping",
                        key,
                        self.prefix,
                    )
                    continue

                suffix = key[len(self.prefix) :]
                await self._handle_expired_kick(suffix)
        except Exception:
            logger.exception("Unexpected error in LobbyOfflineUsersKicker _run() loop")
        finally:
            await pubsub.aclose()
            logger.debug("LobbyOfflineUsersKicker pubsub closed")

    async def _handle_expired_kick(self, suffix: str) -> None:
        try:
            lobby_id_str, user_id_str = suffix.split(":", 1)
            lobby_id = uuid.UUID(lobby_id_str)
            user_id = uuid.UUID(user_id_str)
        except Exception:
            logger.warning(
                "Invalid key suffix in lobby kick key: %s (raw suffix=%r)",
                suffix,
                suffix,
            )
            return

        logger.debug(
            f"Handling offline lobby kick for lobby_id={lobby_id}, user_id={user_id}"
        )

        redis_client = await get_redis_client()

        async with async_session_maker() as db_session:
            lobby_repo = RedisLobbyRepository(redis_client)
            multi_repo = RedisMultiplayerRepository(db_session, redis_client)
            user_repo = UserRepository(db_session)
            notification_system = get_notification_system()
            session_lock = SessionLock(redis_client)

            lobby_service = LobbyService(
                lobby_repo=lobby_repo,
                user_repo=user_repo,
                multi_repo=multi_repo,
                notification_system=notification_system,
                session_lock=session_lock,
            )

            user = await user_repo.get_user(user_id)

            logger.debug(
                "Attempting to remove user %s from lobby %s due to offline timeout",
                user_id,
                lobby_id,
            )

            try:
                await lobby_service.remove_user_from_lobby(lobby_id, user)
                logger.info(
                    "User %s removed from lobby %s due to offline timeout",
                    user_id,
                    lobby_id,
                )
            except LobbyNotExists:
                logger.debug(
                    "Lobby %s does not exist when handling offline kick for user %s",
                    lobby_id,
                    user_id,
                )
            except UserNotInLobby:
                logger.debug(
                    "User %s is not in lobby %s when handling offline kick",
                    user_id,
                    lobby_id,
                )


_kicker_instance = None


async def initialize_lobby_kicker() -> None:
    global _kicker_instance

    if _kicker_instance is None:
        _kicker_instance = LobbyOfflineUsersKicker()

    await _kicker_instance.start()


async def shutdown_lobby_kicker() -> None:
    global _kicker_instance

    if _kicker_instance is not None:
        await _kicker_instance.stop()
        _kicker_instance = None
