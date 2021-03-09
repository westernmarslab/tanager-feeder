import random
from typing import List

def next_rand(range: List) -> int:
    rand = random.random()*(range[1]+1 - range[0])
    return range[0] + int(rand)

i_range = [-70, 70]
e_range = [-70, 70]
az_range = [0, 170]
tray_range = [0, 5]

for i in range(100):
    i = next_rand(i_range)
    e = next_rand(e_range)
    az = next_rand(az_range)
    for i in range(5):
        tray = next_rand(tray_range)
        if tray == 0:
            tray = "WR"
        print(f"move_tray({tray})")
    # print(f"set_goniometer({i}, {e}, {az})")
