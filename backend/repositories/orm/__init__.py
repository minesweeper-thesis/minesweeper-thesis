from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


from .board_orm import *
from .game_orm import *
from .user_orm import *
