from algorithms.boards.functions.moore import moore_neighborhood


def all_fields(
    rows: int,
    columns: int,
    start_field: tuple[int, int],
    already_mined_fields: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    """Function generating all available fields to mine considering the starting field and fields that are already mined.

    Args:
        rows (int): number of rows of the board.
        columns (int): number of columns of the board.
        start_field (tuple[int, int]): starting field coordinates.
        already_mined_fields (list[tuple[int, int]]): list of already mined fields.

    Returns:
        list[tuple[int, int]]: list of available fields.
    """
    fields = set()
    excluded = moore_neighborhood(start_field, rows, columns).union(set((start_field,)))

    for i in range(rows):
        for j in range(columns):
            fields.add((i, j))

    for excluded_field in excluded:
        if excluded_field in fields:
            fields.remove(excluded_field)

    return list(fields.difference(already_mined_fields))
