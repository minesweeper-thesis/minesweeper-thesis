def moore_neighborhood(field : tuple[int,int], rows : int, columns : int) -> set[tuple[int,int]]:
    x, y = field
    fields = set()

    for (a,b) in ((x-1,y-1),(x-1,y),(x-1,y+1),(x,y+1),
                  (x+1,y+1),(x+1,y),(x+1,y-1),(x,y-1)):
        if a >= 0 and a < rows and b >= 0 and b < columns:
            fields.add((a,b))

    return fields