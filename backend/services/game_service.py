from algorithms.boards.random_board import RandomBoard
from algorithms.generator import Generator
from backend.schemas.game import GeneratorInputSchema

from ..db import *
from ..models import *


def generate_random_board(generator_input: GeneratorInputSchema):
    rows = generator_input.rows
    cols = generator_input.columns
    start_field = generator_input.start_field
    mine_count = generator_input.mine_count

    print(rows, cols, start_field, mine_count)
    board = RandomBoard(rows, cols, start_field, mine_count)
    board.grid().print_solved()
    return board.grid().grid


def generate_board(generator_input: GeneratorInputSchema):
    generator = Generator(**generator_input.model_dump())
    return generator.generate().grid().grid
