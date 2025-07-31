from algorithms.generator import Generator
from algorithms.boards.functions.all_fields import all_fields
import time
import random

rows, cols, mine_count = 16, 30, 99
TRIES = 20
fields = all_fields(rows, cols, (-2, -2), [])
fields = [random.choice(fields) for _ in range(TRIES)]
data = []

for i in range(TRIES):
    start = time.time()
    Generator(
        "lightgbm",
        "no",
        (),
        rows,
        cols,
        fields[i],
        mine_count,
        f"algorithms/models/{rows},{cols},{mine_count}_lightgbm100.model",
    ).generate()
    end = time.time()
    data.append(end - start)

print(sum(data))

import matplotlib.pyplot as plt


plt.hist(data, bins=20, edgecolor="black", density=True)
plt.title("Histogram wartości")
plt.xlabel("Wartości")
plt.ylabel("Częstotliwość")
plt.grid(True)

plt.show()
