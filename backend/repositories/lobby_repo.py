import logging
import uuid
from contextlib import suppress
from datetime import datetime, timedelta
from typing import Optional

from fastapi_pagination import Page, Params
from redis.asyncio import Redis
from redis.asyncio.client import Pipeline

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.lobby import Invitation, Lobby, LobbyChatMessage
from backend.lib.redis_client import decode, encode


class LobbyNotFound(Exception):
    pass


class InvitationNotFound(Exception):
    pass


class RedisLobbyRepository(protocols.LobbyRepository):
    def __init__(self, redis: Redis):
        self.redis = redis
        self.lobby_prefix = "lobby:"
        self.invitation_prefix = "invitation:"
        self.message_prefix = "lobby_messages:"
        self.user_lobby_prefix = "lobby_lookup:user:"
        self.user_invitation_prefix = "invitation_lookup:user:"
        self.user_kick_prefix = "lobby_kick:"

    async def save_lobby(self, lobby: Lobby):
        logger.debug(f"save_lobby(lobby_id={lobby.id}, users={len(lobby.users)})")
        lobby_key = f"{self.lobby_prefix}{lobby.id}"
        data = encode(lobby)

        previous_user_ids: set[uuid.UUID] = set()
        existing_lobby_data = await self.redis.get(lobby_key)
        if existing_lobby_data:
            existing_lobby = decode(existing_lobby_data)
            previous_user_ids = {user.id for user in existing_lobby.users}

        current_user_ids = {user.id for user in lobby.users}
        removed_user_ids = previous_user_ids - current_user_ids

        async with self.redis.pipeline() as pipe:
            await pipe.set(lobby_key, data)
            for user in lobby.users:
                await pipe.set(f"{self.user_lobby_prefix}{user.id}", encode(lobby.id))
            for user_id in removed_user_ids:
                await pipe.delete(f"{self.user_lobby_prefix}{user_id}")
                await pipe.delete(f"{self.user_kick_prefix}{lobby.id}:{user_id}")
            await pipe.execute()
        logger.debug(f"Lobby {lobby.id} saved with {len(lobby.users)} users")

    async def get_lobby(self, lobby_id: uuid.UUID) -> Lobby:
        logger.debug(f"get_lobby(lobby_id={lobby_id})")
        data = await self.redis.get(f"{self.lobby_prefix}{lobby_id}")
        if not data:
            raise LobbyNotFound(f"Lobby with id {lobby_id} not found.")
        return decode(data)

    async def delete_lobby(self, lobby_id: uuid.UUID) -> None:
        logger.debug(f"delete_lobby(lobby_id={lobby_id})")
        try:
            lobby = await self.get_lobby(lobby_id)
            async with self.redis.pipeline() as pipe:
                await pipe.delete(f"{self.lobby_prefix}{lobby_id}")
                await pipe.delete(f"{self.message_prefix}{lobby_id}")
                for user in lobby.users:
                    await pipe.delete(f"{self.user_lobby_prefix}{user.id}")
                    await pipe.delete(f"{self.user_kick_prefix}{lobby.id}:{user.id}")
                await pipe.execute()
            logger.info(f"Lobby {lobby_id} deleted")
        except LobbyNotFound:
            pass

    async def _delete_invitations(self, lobby: Lobby, pipe: Pipeline) -> None:
        logger.debug(f"_delete_invitations(lobby_id={lobby.id})")
        for user in lobby.users:
            invitation_ids = await self.redis.smembers(  # type: ignore
                f"{self.user_invitation_prefix}{user.id}"
            )
            for inv_id_bytes in invitation_ids:
                try:
                    inv_id = decode(inv_id_bytes)
                    invitation = await self.get_invitation(inv_id)
                    if invitation.lobby.id == lobby.id:
                        await pipe.delete(f"{self.invitation_prefix}{invitation.id}")
                        await pipe.srem(
                            f"{self.user_invitation_prefix}{invitation.invitee.id}",
                            encode(invitation.id),
                        )  # type: ignore
                        logger.info(
                            f"Deleted invitation {invitation.id} for user {invitation.invitee.id}"
                        )
                except Exception as e:
                    logger.warning(f"Error while deleting invitation {inv_id}: {e}")

    async def save_invitation(self, invitation: Invitation, ttl: timedelta) -> None:
        logger.debug(
            f"save_invitation(invitation_id={invitation.id}, inviter={invitation.inviter.id}, invitee={invitation.invitee.id})"
        )
        data = encode(invitation)
        ttl_seconds = int(ttl.total_seconds())
        async with self.redis.pipeline() as pipe:
            await pipe.set(
                f"{self.invitation_prefix}{invitation.id}", data, ex=ttl_seconds
            )
            await pipe.sadd(
                f"{self.user_invitation_prefix}{invitation.invitee.id}",
                encode(invitation.id),
            )  # type: ignore
            await pipe.execute()
        logger.info(
            f"Invitation {invitation.id} saved from {invitation.inviter.nickname} to {invitation.invitee.nickname}"
        )

    async def get_invitation(self, invitation_id: uuid.UUID) -> Invitation:
        logger.debug(f"get_invitation(invitation_id={invitation_id})")
        data = await self.redis.get(f"{self.invitation_prefix}{invitation_id}")
        if not data:
            raise InvitationNotFound(f"Invitation with id {invitation_id} not found.")
        return decode(data)

    async def delete_invitation(self, invitation_id: uuid.UUID) -> None:
        logger.debug(f"delete_invitation(invitation_id={invitation_id})")
        with suppress(InvitationNotFound):
            invitation = await self.get_invitation(invitation_id)
            async with self.redis.pipeline() as pipe:
                await pipe.delete(f"{self.invitation_prefix}{invitation_id}")
                await pipe.srem(
                    f"{self.user_invitation_prefix}{invitation.invitee.id}",
                    encode(invitation_id),
                )  # type: ignore
                await pipe.execute()
            logger.debug(f"Invitation {invitation_id} deleted")

    async def get_pending_invitations(self, user_id: uuid.UUID) -> list[Invitation]:
        logger.debug(f"get_pending_invitations(user_id={user_id})")
        invitation_ids = await self.redis.smembers(  # type: ignore
            f"{self.user_invitation_prefix}{user_id}"
        )
        invitations = []
        for inv_id_bytes in invitation_ids:
            try:
                inv_id = decode(inv_id_bytes)
                inv = await self.get_invitation(inv_id)
                invitations.append(inv)
            except InvitationNotFound:
                await self.redis.srem(f"{self.user_invitation_prefix}{user_id}", inv_id_bytes)  # type: ignore
        return invitations

    async def get_user_lobby(self, user_id: uuid.UUID) -> Optional[Lobby]:
        logger.debug(f"get_user_lobby(user_id={user_id})")
        lobby_id_bytes = await self.redis.get(f"{self.user_lobby_prefix}{user_id}")
        if lobby_id_bytes:
            try:
                lobby_id = decode(lobby_id_bytes)
                return await self.get_lobby(lobby_id)
            except LobbyNotFound:
                await self.redis.delete(f"{self.user_lobby_prefix}{user_id}")
        return None

    async def add_message(self, message: LobbyChatMessage) -> None:
        logger.debug(
            f"add_message(lobby_id={message.lobby_id}, sender={message.sender.id})"
        )
        data = encode(message)
        await self.redis.lpush(f"{self.message_prefix}{message.lobby_id}", data)  # type: ignore

    async def get_messages(self, lobby_id: uuid.UUID, pagination_params: Params):
        logger.debug(
            f"get_messages(lobby_id={lobby_id}, page={pagination_params.page})"
        )
        key = f"{self.message_prefix}{lobby_id}"
        total = await self.redis.llen(key)  # type: ignore

        start = (pagination_params.page - 1) * pagination_params.size
        end = start + pagination_params.size - 1

        messages_data = await self.redis.lrange(key, start, end)  # type: ignore
        items = [decode(m) for m in messages_data]

        return Page.create(items=items, total=total, params=pagination_params)

    async def set_kick_at(
        self, user_id: uuid.UUID, lobby_id: uuid.UUID, kick_at: datetime | None
    ) -> None:
        key = f"{self.user_kick_prefix}{lobby_id}:{user_id}"

        if kick_at is None:
            logger.debug(
                "Clearing kick time for user %s in lobby %s (deleting key %s)",
                user_id,
                lobby_id,
                key,
            )
            await self.redis.delete(key)
            return

        now = datetime.now()
        ttl_seconds = (kick_at - now).total_seconds()

        if ttl_seconds <= 0:
            logger.debug(
                "Requested kick_at %s for user %s in lobby %s is in the past "
                "(ttl_seconds=%.2f), deleting key %s instead of setting it",
                kick_at,
                user_id,
                lobby_id,
                ttl_seconds,
                key,
            )
            await self.redis.delete(key)
            return

        logger.debug(
            "Setting kick time for user %s in lobby %s at %s (ttl_seconds=%.2f, key=%s)",
            user_id,
            lobby_id,
            kick_at,
            ttl_seconds,
            key,
        )
        await self.redis.set(key, "1", ex=int(ttl_seconds))
