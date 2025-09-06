import time

from algorithms.generator import Generator

"""generator = Generator("lightgbm", "no", (), 16, 30, (4,4), 99)

sum_time = 0
sum_time2 = 0

for _ in range(10):
    s = time.process_time()
    s2 = time.time()
    board = generator.generate()
    e = time.process_time()
    e2 = time.time()
    print(e-s,e2-s2)

    sum_time += e-s
    sum_time2 += e2-s2

print('Average time: ',sum_time/10,sum_time2/10)"""

generator = Generator(
    "lightgbm", "GA", (10, 50, 10, 0.05), 16, 30, (4, 4), 99
)  # nie ma takiego pliku

sum_time = 0
sum_time2 = 0

for _ in range(10):
    s = time.process_time()
    s2 = time.time()
    board = generator.generate()
    e = time.process_time()
    e2 = time.time()
    print(e - s, e2 - s2)

    sum_time += e - s
    sum_time2 += e2 - s2

print("Average time: ", sum_time / 10, sum_time2 / 10)
