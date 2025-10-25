from enum import Enum


class FieldState(Enum):
    MINED = -3
    NOT_MINED = -2
    POSSIBLE_MINE = -1
    NOT_REVEALED_NOT_NEIGHBOUR = 0
    NOT_REVEALED_NEIGHBOUR = 1
    REVEALED = 2
