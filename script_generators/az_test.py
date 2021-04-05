import random
from typing import List

def next_rand(range: List) -> int:
    rand = random.random()*(range[1] - range[0])
    return range[0] + int(rand)

az_range = [0, 170]

for i in range(100):
    az = next_rand(az_range)
    print(f"set_azimuth({az})")