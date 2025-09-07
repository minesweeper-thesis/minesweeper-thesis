from algorithms.boards.board import Board
from algorithms.boards.functions.all_fields import all_fields
import random
from copy import deepcopy


class RandomNeighbourBoard(Board):
    """Board that has the same mined fields as the other one, except for some fixed amount of fields to mine."""

    def __init__(self, other_board: Board, fields_changed: int) -> None:
        """Initializes board that has the same mined fields as the other one, except for some fixed amount of fields to mine.

        Args:
            other_board (Board): base board.
            fields_changed (int): number of fields to change.
        """
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

        Board.__init__(
            self,
            other_board.rows,
            other_board.columns,
            other_board.start_field,
            other_board.mine_count,
            mined_fields[: other_board.mine_count],
        )
