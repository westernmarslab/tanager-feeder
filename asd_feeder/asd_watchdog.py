import os
import time


class Watchdog:
    def __init__(self):
        home_loc = os.path.expanduser("~")
        temp_data_loc = os.path.join(home_loc, "Tanager", "temp_data")
        self.folder = temp_data_loc

    def watch(self):
        announced_minute = []
        next_minute = 60
        time_since_cycled = 0
        while True:
            print("Watching")
            files = os.listdir(self.folder)
            for file in files:
                if "watchdog" in file:
                    try:
                        os.remove(os.path.join(self.folder, file))
                    except: # OSError?
                        print("Warning: Could not delete watchdog file.")
                    time_since_cycled = 0
            print(time_since_cycled)
            if next_minute < time_since_cycled and len(announced_minute) == next_minute/60-1:
                print(f"{time_since_cycled/60} minutes since watchdog reset. Restarting computer at 15 minutes.")
                announced_minute.append(1)
                next_minute += 60
            elif 900 < time_since_cycled:
                home = os.path.expanduser("~")
                with open(os.path.join(home, "watchdog_restart"), "w+") as f:
                    f.write("watched!")
                print("15 minutes since cycle, time for restart")
                time.sleep(30)
                os.system("shutdown /r /t 1")

            time.sleep(10)
            time_since_cycled += 10

def main():
    watcher = Watchdog()
    watcher.watch()