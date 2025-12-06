import uuid
from dataclasses import dataclass


@dataclass
class KickedFromLobby:
    lobby_id: uuid.UUID


__all__ = ["KickedFromLobby"]
