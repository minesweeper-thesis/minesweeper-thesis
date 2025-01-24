import random
import time

def moore_neighborhood(field, rows, columns):
    x, y = field
    fields = set()

    for (a,b) in ((x-1,y-1),(x-1,y),(x-1,y+1),(x,y+1),
                  (x+1,y+1),(x+1,y),(x+1,y-1),(x,y-1)):
        if a >= 0 and a < rows and b >= 0 and b < columns:
            fields.add((a,b))

    return fields

def all_fields(rows, columns, field):
    fields = set()
    excluded = moore_neighborhood(field, rows, columns).union(set((field,)))
    
    for i in range(rows):
        for j in range(columns):
            fields.add((i,j))
    
    for excluded_field in excluded:
        fields.remove(excluded_field)
    
    return list(fields)

def naive_board(rows, columns, field, count):
    board = [[0 for _ in range(columns)] for _ in range(rows)]
    fields = all_fields(rows,columns,field)
    mined_fields = []
    random.shuffle(fields)

    for i in range(count):
        x, y = fields[i]
        mined_fields.append(fields[i])
        board[x][y] = 9

        neighborhood = moore_neighborhood((x,y),rows,columns)
        for x_n, y_n in neighborhood:
            board[x_n][y_n] = min(9,board[x_n][y_n]+1)
    
    return board, mined_fields

def crossover(mined_fields1, mined_fields2, rows, columns, field):
    count = len(mined_fields1)
    fields = set(mined_fields1 + mined_fields2)
    other_fields = list(set(all_fields(rows,columns,field)).difference(fields))
    random.shuffle(other_fields)
    fields = list(fields)
    fields.extend(other_fields[:2])
    random.shuffle(fields)
    mined_fields = fields[:count]

    board = [[0 for _ in range(columns)] for _ in range(rows)]
    for i in range(count):
        x, y = mined_fields[i]
        board[x][y] = 9

        neighborhood = moore_neighborhood((x,y),rows,columns)
        for x_n, y_n in neighborhood:
            board[x_n][y_n] = min(9,board[x_n][y_n]+1)
    
    return board, mined_fields

def evaluate(board): # funkcja celu: tutaj dajemy przykładowe zadanie, żeby zmaksymalizować w macierzy wartości w pierwszych trzech wierszach i zminimalizować w pozostałych; zamiast tej funkcji będzie model szacujący, czy plansza jest deterministyczna
    return sum(board[0])+sum(board[1])+sum(board[2])-sum(board[3])-sum(board[4])-sum(board[5])-sum(board[6])-sum(board[7])

start_field = (4,4)
rows = 16
columns = 30
count = 99
generations = 100
population_size = 50
parents_count = 10
per_random = 10
population = [naive_board(rows,columns,start_field,count) for _ in range(population_size)]

for generation in range(generations):
    ranking = [(evaluate(population[i][0]), i) for i in range(population_size)]

    ranking.sort(key=lambda x: -x[0])

    parents = [id for score, id in ranking[:parents_count]]

    for i in range(population_size):
        if i not in parents:
            mined_fields1 = population[parents[random.randint(0,parents_count-1)]][1]
            mined_fields2 = population[parents[random.randint(0,parents_count-1)]][1]
            population[i] = crossover(mined_fields1,mined_fields2,rows,columns,start_field)

            if random.randint(0,per_random-1) == 0:
                population[i] = naive_board(rows,columns,start_field,count)

board, mined_fields = population[parents[0]]

for row in board:
    print(row)

print(evaluate(board))