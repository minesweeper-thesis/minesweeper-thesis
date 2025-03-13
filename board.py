from moore import moore_neighborhood
import numpy as np

class Board:
    def board(self) -> list[list[int]]:
        board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]

        for i in range(len(self.mined_fields)):
            x, y = self.mined_fields[i]
            board[x][y] = 9

            neighborhood = moore_neighborhood((x,y),self.rows,self.columns)
            for x_n, y_n in neighborhood:
                board[x_n][y_n] = min(9,board[x_n][y_n]+1)
        
        return board

    def model_input(self) -> np.ndarray: # input do modeli, rozwążyć jakąś standaryzację
        temp = [[0 for _ in range(self.columns)] for _ in range(self.rows)]
        for (i, j) in self.mined_fields:
            temp[i][j] = 1

        distances = [[(self.start_field[0]-j)**2+(self.start_field[1]-i)**2 for i in range(self.columns)] for j in range(self.rows)]
        temp.extend(distances)
        
        return np.array(temp)

    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int, mined_fields: list[tuple[int,int]]) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count
        self.mined_fields = mined_fields