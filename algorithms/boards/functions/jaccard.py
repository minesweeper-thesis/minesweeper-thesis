from algorithms.boards.base_board import BaseBoard


def jaccard_score(board1: BaseBoard, board2: BaseBoard) -> float:
    mines1 = set(board1.mined_fields)
    mines2 = set(board2.mined_fields)

    all_mines = mines1.union(mines2)
    mines_in_both = set()

    for mine in all_mines:
        if mine in mines1 and mine in mines2:
            mines_in_both.add(mine)

    return len(mines_in_both) / len(all_mines)


def jaccard_distance(board1: BaseBoard, board2: BaseBoard) -> float:
    return 1 - jaccard_score(board1, board2)
