import logging
import pickle
import uuid
from collections import defaultdict
from contextlib import suppress
from typing import Optional

from fastapi_pagination import Page, Params
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

from backend import protocols
from backend.core.lobby import Invitation, Lobby, LobbyChatMessage
from backend.lib.redis_client import redis_client


class LobbyNotFound(Exception):
    pass


class InvitationNotFound(Exception):
    pass


class InMemoryLobbyRepository(protocols.LobbyRepository):
    def __init__(self):
        self.lobbies: dict[uuid.UUID, Lobby] = {}
        self.invitations: dict[uuid.UUID, Invitation] = {}
        self.messages: dict[uuid.UUID, list[LobbyChatMessage]] = defaultdict(list)

    async def save_lobby(self, lobby: Lobby):
        logger.debug(f"save_lobby(lobby_id={lobby.id}, users={len(lobby.users)})")
        self.lobbies[lobby.id] = lobby
        logger.debug(f"Lobby {lobby.id} saved with {len(lobby.users)} users")

    async def get_lobby(self, lobby_id: uuid.UUID) -> Lobby:
        logger.debug(f"get_lobby(lobby_id={lobby_id})")
        try:
            return self.lobbies[lobby_id]

        except KeyError:
            raise LobbyNotFound(f"Lobby with id {lobby_id} not found.") from None

    async def delete_lobby(self, lobby_id: uuid.UUID) -> None:
        logger.debug(f"delete_lobby(lobby_id={lobby_id})")
        with suppress(KeyError):
            del self.lobbies[lobby_id]
            logger.info(f"Lobby {lobby_id} deleted")

    async def save_invitation(self, invitation: Invitation):
        logger.debug(
            f"save_invitation(invitation_id={invitation.id}, inviter={invitation.inviter.id}, invitee={invitation.invitee.id})"
        )
        self.invitations[invitation.id] = invitation
        logger.info(
            f"Invitation {invitation.id} saved from {invitation.inviter.nickname} to {invitation.invitee.nickname}"
        )

    async def get_invitation(self, invitation_id: uuid.UUID) -> Invitation:
        logger.debug(f"get_invitation(invitation_id={invitation_id})")
        try:
            return self.invitations[invitation_id]

        except KeyError:
            raise InvitationNotFound(
                f"Invitation with id {invitation_id} not found."
            ) from None

    async def delete_invitation(self, invitation_id: uuid.UUID) -> None:
        logger.debug(f"delete_invitation(invitation_id={invitation_id})")
        with suppress(KeyError):
            del self.invitations[invitation_id]
            logger.debug(f"Invitation {invitation_id} deleted")

    async def get_pending_invitations(self, user_id: uuid.UUID) -> list[Invitation]:
        logger.debug(f"get_pending_invitations(user_id={user_id})")
        return [
            invitation
            for invitation in self.invitations.values()
            if invitation.invitee.id == user_id
        ]

    async def get_user_lobby(self, user_id: uuid.UUID) -> Optional[Lobby]:
        logger.debug(f"get_user_lobby(user_id={user_id})")
        for lobby in self.lobbies.values():
            if any(user.id == user_id for user in lobby.users):
                return lobby
        return None

    async def add_message(self, message: LobbyChatMessage) -> None:
        logger.debug(
            f"add_message(lobby_id={message.lobby_id}, sender={message.sender.id})"
        )
        self.messages[message.lobby_id].append(message)

    async def get_messages(self, lobby_id: uuid.UUID, pagination_params: Params):
        logger.debug(
            f"get_messages(lobby_id={lobby_id}, page={pagination_params.page})"
        )
        all_messages = self.messages[lobby_id]
        start = (pagination_params.page - 1) * pagination_params.size
        end = start + pagination_params.size
        items = sorted(all_messages, key=lambda msg: msg.timestamp, reverse=True)[
            start:end
        ]
        return Page.create(
            items=items, total=len(all_messages), params=pagination_params
        )


class RedisLobbyRepository(protocols.LobbyRepository):
    def __init__(self):
        self.redis: Redis = redis_client  # type: ignore
        self.lobby_prefix = "lobby:"
        self.invitation_prefix = "invitation:"
        self.message_prefix = "lobby_messages:"
        self.user_lobby_prefix = "lobby_lookup:user:"
        self.user_invitation_prefix = "invitation_lookup:user:"

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
                inv = await self.get_invitation(uuid.UUID(inv_id))
                invitations.append(inv)
            except InvitationNotFound:
                await self.redis.srem(f"{self.user_invitation_prefix}{user_id}", inv_id)  # type: ignore
        return invitations

    async def get_user_lobby(self, user_id: uuid.UUID) -> Optional[Lobby]:
        logger.debug(f"get_user_lobby(user_id={user_id})")
        lobby_id_str = await self.redis.get(f"{self.user_lobby_prefix}{user_id}")
        if lobby_id_str:
            try:
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
