def moore_neighborhood(
    field: tuple[int, int], rows: int, columns: int
) -> set[tuple[int, int]]:
    """Function returning fields in the moore neighborhood of a given field considering edges of the board.

    Args:
        field (tuple[int, int]): coordinates of the field.
        rows (int): number of rows of the board.
        columns (int): number of columns of the board.

    Returns:
        set[tuple[int, int]]: set containing fields from the moore neighborhood.
    """
    x, y = field
    fields = set()

    for a, b in (
        (x - 1, y - 1),
        (x - 1, y),
        (x - 1, y + 1),
        (x, y + 1),
        (x + 1, y + 1),
        (x + 1, y),
        (x + 1, y - 1),
        (x, y - 1),
    ):
        if a >= 0 and a < rows and b >= 0 and b < columns:
            fields.add((a, b))

    return fields
