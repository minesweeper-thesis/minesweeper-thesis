import random

def moore_neighborhood(field : tuple[int,int], rows : int, columns : int) -> set[tuple[int,int]]:
    x, y = field
    fields = set()

    for (a,b) in ((x-1,y-1),(x-1,y),(x-1,y+1),(x,y+1),
                  (x+1,y+1),(x+1,y),(x+1,y-1),(x,y-1)):
        if a >= 0 and a < rows and b >= 0 and b < columns:
            fields.add((a,b))

    return fields

def all_fields(rows : int, columns : int, field : tuple[int,int]) -> list[tuple[int,int]]:
    fields = set()
    excluded = moore_neighborhood(field, rows, columns).union(set((field,)))
    
    for i in range(rows):
        for j in range(columns):
            fields.add((i,j))
    
    for excluded_field in excluded:
        fields.remove(excluded_field)
    
    return list(fields)

class Board:
    def __naive_mined_fields(self) -> list[tuple[int,int]]:
        fields = all_fields(self.rows,self.columns,self.start_field)
        random.shuffle(fields)

        return fields[:self.mine_count]
    
    def __generate_board(self) -> list[list[int]]:
        board = [[0 for _ in range(self.columns)] for _ in range(self.rows)]

        for i in range(len(self.mined_fields)):
            x, y = self.mined_fields[i]
            board[x][y] = 9

            neighborhood = moore_neighborhood((x,y),self.rows,self.columns)
            for x_n, y_n in neighborhood:
                board[x_n][y_n] = min(9,board[x_n][y_n]+1)
        
        return board

    def __init__(self, rows : int, columns : int, start_field : tuple[int,int], mine_count : int) -> None:
        self.rows = rows
        self.columns = columns
        self.start_field = start_field
        self.mine_count = mine_count
    
        self.mined_fields = self.__naive_mined_fields()
        self.board = self.__generate_board()
    
    def crossover(self, board1 : 'Board', board2 : 'Board') -> None:
        self.rows = board1.rows
        self.columns = board1.columns
        self.start_field = board1.start_field
        self.mine_count = board1.mine_count

        count = len(board1.mined_fields)
        fields = set(board1.mined_fields + board2.mined_fields)
        other_fields = list(set(all_fields(self.rows,self.columns,self.start_field)).difference(fields))
        random.shuffle(other_fields)
        fields = list(fields)
        fields.extend(other_fields[:2])
        random.shuffle(fields)
        self.mined_fields = fields[:count]
        self.board = self.__generate_board()

def evaluate(board): # funkcja celu: tutaj dajemy przykładowe zadanie, żeby zmaksymalizować w macierzy wartości w pierwszych trzech wierszach i zminimalizować w pozostałych; zamiast tej funkcji będzie model szacujący, czy plansza jest deterministyczna
    board = board.board
    return sum(board[0])+sum(board[1])+sum(board[2])-sum(board[3])-sum(board[4])-sum(board[5])-sum(board[6])-sum(board[7])

start_field = (4,4)
rows = 9
columns = 9
count = 10
generations = 100
population_size = 50
parents_count = 10
random_specimens = 4
population = [Board(rows,columns,start_field,count) for _ in range(population_size)]

for generation in range(generations):
    ranking = [(evaluate(population[i]), i) for i in range(population_size)]

    ranking.sort(key=lambda x: -x[0])

    parents = [id for score, id in ranking[:parents_count]]

    for i in range(population_size):
        if i not in parents:
            if random.uniform(0,1) < random_specimens/(population_size-parents_count):
                population[i] = Board(rows,columns,start_field,count)
                continue
            
            parent1 = population[parents[random.randint(0,parents_count-1)]]
            parent2 = population[parents[random.randint(0,parents_count-1)]]
            population[i].crossover(parent1,parent2)
                

best = population[parents[0]]

for row in best.board:
    print(row)

print(evaluate(best))