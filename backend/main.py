from fastapi import FastAPI
from algorithms.random_board import RandomBoard
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Konfiguracja CORS niezbyt specyficzna, ale chciałem coś co działa bez zabawy
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/board")
async def get_board(rows: int, cols: int, start_x: int, start_y: int, mine_count: int):
    print(rows, cols, (start_x, start_y), mine_count)
    board = RandomBoard(rows, cols, (start_x, start_y), mine_count)
    board.grid().print_solved()
    return board.grid().grid
