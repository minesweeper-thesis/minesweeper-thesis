from algorithms.boards.base_board import BaseBoard
from algorithms.boards.functions.all_fields import all_fields
import random
from copy import deepcopy


class RandomNeighbourBoard(BaseBoard):
    def __init__(self, other_board: BaseBoard, fields_changed: int) -> None:
        mined_fields = deepcopy(other_board.mined_fields)
        new_mined_fields = random.sample(
            all_fields(
                other_board.rows,
                other_board.columns,
                other_board.start_field,
                mined_fields,
            ),
            k=fields_changed,
        )
        random.shuffle(mined_fields)
        mined_fields = new_mined_fields + mined_fields

        BaseBoard.__init__(
            self,
            other_board.rows,
            other_board.columns,
            other_board.start_field,
            other_board.mine_count,
            mined_fields[: other_board.mine_count],
        )
