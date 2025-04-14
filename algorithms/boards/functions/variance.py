import numpy as np


# function that takes a list of matrices in 0-1 form and returns their variance - will be used to see if our solutions are not too similar
def variance(matrices: list[np.ndarray]) -> float:
    mean_matrix = np.mean(matrices, axis=0)
    return np.mean(
        [np.linalg.norm(matrix - mean_matrix, "fro") ** 2 for matrix in matrices]
    )
