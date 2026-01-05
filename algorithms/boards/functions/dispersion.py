from algorithms.boards.base_board import BaseBoard
from algorithms.boards.functions.jaccard import jaccard_distance


def dispersion(boards: list[BaseBoard]):
    return (
        sum(jaccard_distance(b1, b2) ** 2 for b2 in boards for b1 in boards)
        / len(boards) ** 2
    )
