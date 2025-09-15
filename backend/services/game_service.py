from algorithms.boards.random_board import RandomBoard
from algorithms.generator import Generator
from backend.schemas import GeneratorInput


class GameService:
    def generate_random_board(self, generator_input: GeneratorInput):
        rows = generator_input.rows
        cols = generator_input.columns
        start_field = generator_input.start_field
        mine_count = generator_input.mine_count

        board = RandomBoard(rows, cols, start_field, mine_count)
        board.grid().print_solved()
        return board.grid().grid

    def generate_board(self, generator_input: GeneratorInput):
        generator = Generator(
            **generator_input.model_dump(), classifier_iterations=6400
        )
        return generator.generate().grid().grid
