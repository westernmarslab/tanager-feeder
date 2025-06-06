import time
from typing import List

from tanager_feeder.commanders.commander import Commander
from tanager_feeder.utils import MovementUnits


class PiCommander(Commander):
    def configure(self, i: int, e: int, pos: str):
        self.remove_from_listener_queue(["piconfigsuccess"])
        filename = self.encrypt("configure", [i, e, pos])
        self.send(filename)
        return filename

    def get_current_position(self) -> List:
        self.remove_from_listener_queue(["currentposition"])
        filename = self.encrypt("getcurrentposition")
        self.send(filename)
        return filename

    # We may specify either an incidence angle to move to, or a number of steps to move
    def set_incidence(self, num: int, unit: str = MovementUnits.ANGLE.value):
        self.remove_from_listener_queue(["donemoving", "nopiconfig"])
        if unit == MovementUnits.ANGLE.value:
            incidence = num
            filename = self.encrypt("moveincidence", [incidence])
        else:
            steps = num
            filename = self.encrypt("moveincidence", [steps, "steps"])
        self.send(filename)
        return filename

    # We may specify either an azimuth angle to move to, or a number of steps to move
    def set_azimuth(self, num: int, unit: str = MovementUnits.ANGLE.value):
        self.remove_from_listener_queue(["donemoving", "nopiconfig"])
        if unit == MovementUnits.ANGLE.value:
            azimuth = num
            filename = self.encrypt("moveazimuth", [azimuth])
        else:
            steps = num
            filename = self.encrypt("moveazimuth", [steps, "steps"])
        self.send(filename)
        return filename

    # We may specify either an emission angle to move to, or a number of steps to move
    def set_emission(self, num: int, unit: str = MovementUnits.ANGLE.value):
        self.remove_from_listener_queue(["donemoving", "nopiconfig"])
        if unit == MovementUnits.ANGLE.value:
            emission = num
            filename = self.encrypt("moveemission", [emission])
        else:
            steps = num
            filename = self.encrypt("moveemission", [steps, "steps"])
        self.send(filename)
        return filename

    # pos can be either a sample position, or a number of motor steps.
    def move_tray(self, pos: str, unit: str):
        self.remove_from_listener_queue(["donemoving"])
        if unit == MovementUnits.POSITION.value:
            positions = {
                "wr": "wr",
                "WR": "wr",
                "Sample 1": "one",
                "Sample 2": "two",
                "Sample 3": "three",
                "Sample 4": "four",
                "Sample 5": "five",
            }
            if pos in positions:
                filename = self.encrypt("movetray", [positions[pos]])
            else:
                print(filename)
                raise Exception("Invalid position")
        else:
            filename = self.encrypt("movetray", [pos, "steps"])
        self.send(filename)

    def send(self, message: str):
        sent = False
        attempt = 1
        while sent is False and attempt < 10:
            sent = self.connection_manager.send_to_pi(message)
            attempt += 1
            if not sent:
                print(f"Retrying command {message}")
                time.sleep(4)
        if not sent:
            print(f"Failed to send command {message}")
        else:
            print(f"Sent {message}")
        return sent
