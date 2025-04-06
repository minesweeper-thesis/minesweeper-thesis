import json
import os
from algorithms.random_board import RandomBoard
from algorithms.is_solvable import is_solvable

class DataGenerator:
    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count

        self.filename = 'data/'+str(rows)+'#'+str(columns)+'#'+str(start_field[0])+'#'+str(start_field[1])+'#'+str(mine_count)+'.json'
    
    def generate(self, count : int) -> None:
        if not os.path.exists(self.filename):
            data = []
        else:
            with open(self.filename, "r") as f:
                data = json.load(f)

        for _ in range(count):
            board = RandomBoard(self.rows, self.columns, self.start_field, self.mine_count)
            solvable = is_solvable(board)
            board_json = board.to_json()
            board_json['solvable'] = solvable
            data.append(board_json)
        
        with open(self.filename, "w") as f:
            for instance in data:
                json.dump(instance, f)
                f.write('\n')