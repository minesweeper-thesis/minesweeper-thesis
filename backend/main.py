from fastapi import FastAPI

from algorithms.random_board import RandomBoard

app = FastAPI()


@app.get("/board")
async def get_board(rows: int, cols: int, start_x: int, start_y: int, mine_count: int):
    print(rows, cols, (start_x, start_y), mine_count)
    board = RandomBoard(rows, cols, (start_x, start_y), mine_count)
    return board.board()
