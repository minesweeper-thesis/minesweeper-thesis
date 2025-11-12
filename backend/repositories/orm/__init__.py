from sqlalchemy.orm import declarative_base

Base = declarative_base()

from .board_orm import *
from .game_orm import *
from .user_orm import *
