from algorithms.moore import moore_neighborhood

def all_fields(rows : int, columns : int, field : tuple[int,int]) -> list[tuple[int,int]]:
    fields = set()
    excluded = moore_neighborhood(field, rows, columns).union(set((field,)))
    
    for i in range(rows):
        for j in range(columns):
            fields.add((i,j))
    
    for excluded_field in excluded:
        fields.remove(excluded_field)
    
    return list(fields)