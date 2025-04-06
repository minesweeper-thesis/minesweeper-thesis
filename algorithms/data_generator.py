import json
import os
import random
from algorithms.random_board import RandomBoard
from algorithms.all_fields import all_fields
from algorithms.is_solvable import is_solvable

class DataGenerator:
    def __init__(self, rows : int, columns : int, mine_count : int) -> None:
        self.rows = rows
        self.columns = columns
        self.mine_count = mine_count

        self.filename = 'data/'+str(rows)+','+str(columns)+',' + str(mine_count) + '.json'
    
    def generate(self, count : int) -> None:
        if not os.path.exists(self.filename):
            data = []
        else:
            with open(self.filename, "r") as f:
                data = []
                for line in f:
                    data.append(json.loads(line))
        
        fields = all_fields(self.rows, self.columns, (-2,-2))

        for _ in range(count):
            start_field = fields[random.randint(0,len(fields)-1)]
            board = RandomBoard(self.rows, self.columns, start_field, self.mine_count)
            solvable = is_solvable(board)
            board_json = board.to_json()
            board_json['solvable'] = solvable
            data.append(board_json)
        
        with open(self.filename, "w") as f:
            for instance in data:
                json.dump(instance, f)
                f.write('\n')

a = DataGenerator(10, 10, 15)
a.generate(970)