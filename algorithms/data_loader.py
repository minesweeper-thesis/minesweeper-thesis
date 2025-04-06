from algorithms.board import Board
import json

class DataLoader:
    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count

        self.filename = 'data/'+str(rows)+'#'+str(columns)+'#'+str(start_field[0])+'#'+str(start_field[1])+'#'+str(mine_count)+'.json'
    
    def load(self) -> list[tuple[Board,bool]]:
        result = []

        with open(self.filename,"r") as f:
            for line in f:
                board_json = json.loads(line)
                board = Board(self.rows, self.columns, self.start_field, self.mine_count, [tuple(pos) for pos in board_json['mined_fields']])
                result.append((board,board_json['solvable']))
        
        return result