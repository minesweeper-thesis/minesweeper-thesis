from algorithms.boards.base_board import BaseBoard
from algorithms.boards.functions.jaccard import jaccard_distance


def variance(boards: list[BaseBoard]):
    sum_distances = 0.0
    n = len(boards)

    for i in range(n):
        for j in range(i + 1, n):
            sum_distances += jaccard_distance(boards[i], boards[j])

    return sum_distances / (n * (n - 1) / 2)
