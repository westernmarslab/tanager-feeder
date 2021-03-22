import random
from typing import List

def next_rand(range: List) -> int:
    rand = random.random()*(range[1] - range[0])
    return range[0] + int(rand)

i_range = [-70, 70]
e_range = [-70, 70]
az_range = [0, 170]

for i in range(10):
    i = next_rand(i_range)
    e = next_rand(e_range)
    az = next_rand(az_range)
    print(f"set_display({i}, {e}, {az})")