from typing import Self

from pydantic import BaseModel

from backend.core.game import *
from backend.core.lobby import *


class Response(ABC, BaseModel):
    @classmethod
    @abstractmethod
    def from_core(cls, data) -> Self:
        """Create response from domain object."""
        ...
