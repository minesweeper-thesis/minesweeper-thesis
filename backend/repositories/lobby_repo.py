import logging
import pickle
import uuid
from contextlib import suppress
from datetime import datetime
from typing import Optional

from fastapi_pagination import Page, Params
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.lobby import Invitation, Lobby, LobbyChatMessage
from backend.lib.redis_client import decode_redis_value


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
        data = pickle.dumps(lobby)
        async with self.redis.pipeline() as pipe:
            await pipe.set(f"{self.lobby_prefix}{lobby.id}", data)
            for user in lobby.users:
                await pipe.set(f"{self.user_lobby_prefix}{user.id}", str(lobby.id))
            await pipe.execute()
        logger.debug(f"Lobby {lobby.id} saved with {len(lobby.users)} users")

    async def get_lobby(self, lobby_id: uuid.UUID) -> Lobby:
        logger.debug(f"get_lobby(lobby_id={lobby_id})")
        data = await self.redis.get(f"{self.lobby_prefix}{lobby_id}")
        if not data:
            raise LobbyNotFound(f"Lobby with id {lobby_id} not found.")
        return pickle.loads(data)

    async def delete_lobby(self, lobby_id: uuid.UUID) -> None:
        logger.debug(f"delete_lobby(lobby_id={lobby_id})")
        try:
            lobby = await self.get_lobby(lobby_id)
            async with self.redis.pipeline() as pipe:
                await pipe.delete(f"{self.lobby_prefix}{lobby_id}")
                await pipe.delete(f"{self.message_prefix}{lobby_id}")
                for user in lobby.users:
                    await pipe.delete(f"{self.user_lobby_prefix}{user.id}")
                await pipe.execute()
            logger.info(f"Lobby {lobby_id} deleted")
        except LobbyNotFound:
            pass

    async def save_invitation(self, invitation: Invitation):
        logger.debug(
            f"save_invitation(invitation_id={invitation.id}, inviter={invitation.inviter.id}, invitee={invitation.invitee.id})"
        )
        data = pickle.dumps(invitation)
        async with self.redis.pipeline() as pipe:
            await pipe.set(f"{self.invitation_prefix}{invitation.id}", data)
            await pipe.sadd(
                f"{self.user_invitation_prefix}{invitation.invitee.id}",
                str(invitation.id),
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
        return pickle.loads(data)

    async def delete_invitation(self, invitation_id: uuid.UUID) -> None:
        logger.debug(f"delete_invitation(invitation_id={invitation_id})")
        with suppress(InvitationNotFound):
            invitation = await self.get_invitation(invitation_id)
            async with self.redis.pipeline() as pipe:
                await pipe.delete(f"{self.invitation_prefix}{invitation_id}")
                await pipe.srem(
                    f"{self.user_invitation_prefix}{invitation.invitee.id}",
                    str(invitation_id),
                )  # type: ignore
                await pipe.execute()
            logger.debug(f"Invitation {invitation_id} deleted")

    async def get_pending_invitations(self, user_id: uuid.UUID) -> list[Invitation]:
        logger.debug(f"get_pending_invitations(user_id={user_id})")
        invitation_ids = await self.redis.smembers(  # type: ignore
            f"{self.user_invitation_prefix}{user_id}"
        )
        invitations = []
        for inv_id in invitation_ids:
            try:
                inv_id_str = decode_redis_value(inv_id)
                inv = await self.get_invitation(uuid.UUID(inv_id_str))
                invitations.append(inv)
            except InvitationNotFound:
                await self.redis.srem(f"{self.user_invitation_prefix}{user_id}", inv_id)  # type: ignore
        return invitations

    async def get_user_lobby(self, user_id: uuid.UUID) -> Optional[Lobby]:
        logger.debug(f"get_user_lobby(user_id={user_id})")
        lobby_id_str = await self.redis.get(f"{self.user_lobby_prefix}{user_id}")
        if lobby_id_str:
            try:
                lobby_id_str = decode_redis_value(lobby_id_str)
                return await self.get_lobby(uuid.UUID(lobby_id_str))
            except LobbyNotFound:
                await self.redis.delete(f"{self.user_lobby_prefix}{user_id}")
        return None

    async def add_message(self, message: LobbyChatMessage) -> None:
        logger.debug(
            f"add_message(lobby_id={message.lobby_id}, sender={message.sender.id})"
        )
        data = pickle.dumps(message)
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
        items = [pickle.loads(m) for m in messages_data]

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
