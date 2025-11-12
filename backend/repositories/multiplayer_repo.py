from backend.db.db import DBSession

from .exceptions import *
from .orm import *


class MultiplayerRepository:
    def __init__(self, session: DBSession):
        self.session = session
