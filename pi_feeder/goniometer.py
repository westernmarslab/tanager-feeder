from threading import Thread
import time
from typing import Tuple, Union

import numpy as np
from pi_feeder import motor, encoder, limit_switch

AZIMUTH_GEAR_RATIO = 10
AZIMUTH_HOME_OFFSET = 24.7
DISTANCE_TOLERANCE = 0.5


class Goniometer:
    def __init__(self, i_zero: float = 0, e_zero: float = 0, az_zero: float = 0, tray_zero: float = 0):
        # JK changed GPIO pinouts to match box wiring.
        self.motors = {
            "incidence": {
                "motor": motor.Motor(
                    "Incidence",
                    [6, 5],
                    [],
                    17,  # 6400 steps/rev
                    0.003,
                    encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x48, zero_position=i_zero),
                    1,
                ),
                "gear ratio": 1,
                "position conversion": self.science_i_to_motor_i,
            },
            "emission": {
                "motor": motor.Motor(
                    "Emission",
                    [23, 22],
                    [],
                    4.4,  # 1600 steps/rev
                    0.003,
                    encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x4C, zero_position=e_zero),
                    1,
                ),
                "gear ratio": 1,
                "position conversion": self.science_e_to_motor_e,
            },
            "azimuth": {  # this one has limit switches and a gear ratio of 10
                "motor": motor.Motor(
                    "Azimuth",
                    [27, 17],
                    [limit_switch.LimitSwitch(2), limit_switch.LimitSwitch(3)],
                    1.11,  # 800 steps/rev
                    0.007,
                    encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x50, zero_position=az_zero),
                    AZIMUTH_GEAR_RATIO,
                ),
                "gear ratio": AZIMUTH_GEAR_RATIO,
                "position conversion": self.science_az_to_motor_az,
            },
            "sample tray": {
                "motor": motor.Motor(
                    "Sample tray",
                    [25, 24],
                    [],
                    8.8,  # 3200 steps per rev
                    0.006,
                    encoder.AMT212ARotaryEncoder(port="/dev/ttyUSB0", encoder_base=0x54, zero_position=tray_zero),
                    1,
                    True, # ok to wrap around to reach positioin
                ),
                "gear ratio": 1,
                "positions": {
                    "-1": 0,
                    "0": 0,
                    "wr": 0,
                    "one": 60,
                    "1": 60,
                    "two": 120,
                    "2": 120,
                    "three": 180,
                    "3": 180,
                    "four": 240,
                    "4": 240,
                    "five": 300,
                    "5": 300,
                },
                "position conversion": self.tray_pos_to_tray_angle,
            },
        }

    @property
    def incidence(self):
        self._incidence = self.motor_i_to_science_i(self.motors["incidence"]["motor"].position_degrees)
        return self._incidence

    @incidence.setter
    def incidence(self, theta):
        raise Exception(
            "Goniometer incidence should not be set directly, should be read from the incidence motor instead."
        )

    @property
    def emission(self):
        return self.motor_e_to_science_e(self.motors["emission"]["motor"].position_degrees)

    @emission.setter
    def emission(self, theta):
        raise Exception(
            "Goniometer emission should not be set directly, should be read from the emission motor instead."
        )

    @property
    def azimuth(self):
        return self.motor_az_to_science_az(
            self.motors["azimuth"]["motor"].position_full_turns, self.motors["azimuth"]["motor"].position_degrees
        )

    @azimuth.setter
    def azimuth(self, theta):
        raise Exception("Goniometer azimuth should not be set directly, should be read from the azimuth motor instead.")

    @property
    def tray_angle(self):
        return self.motors["sample tray"]["motor"].position_degrees

    @tray_angle.setter
    def tray_angle(self, theta):
        raise Exception(
            "Goniometer tray position should not be set directly, should be read from the tray motor instead."
        )

    @property
    def tray_pos(self):
        pos_options = {
            0: "-1",
            60: "0",
            120: "1",
            180: "2",
            240: "3",
            300: "4",
            360: "-1",
        }
        position_degrees = int(self.motors["sample tray"]["motor"].position_degrees)
        #Ok to be off by +/- 1 degree

        if str(position_degrees)[-1] == 9:
            position_degrees += 1

        elif str(position_degrees)[-1] ==1:
            position_degrees -= 1
        if (position_degrees + 1)%10 == 0:
            position_degrees = position_degrees + 1
        elif (position_degrees -1)%10 == 0:
            position_degrees = position_degrees -1
        try:
            return pos_options[position_degrees]
        except KeyError:
            print("UNKNOWN")
            return "unknown"

    @tray_pos.setter
    def tray_pos(self, theta):
        raise Exception(
            "Goniometer tray position should not be set directly, should be read from the tray motor instead."
        )

    def set_position(self, motor_name, target):
        self.motors[motor_name]["motor"].kill_now = False
        self.motors[motor_name]["motor"].update_position(3)
        motor_angle, motor_turns = self.motors[motor_name]["position conversion"](target)

        if motor_name == "azimuth":
            self.motors[motor_name]["motor"].set_full_turns(motor_turns)  # limit switches prevent catastrophe

        last_distance, _ = self.motors[motor_name]["motor"].get_distance_and_direction(motor_angle)
        thread = Thread(target=self.motors[motor_name]["motor"].move_to_angle, args=(motor_angle,))
        thread.start()
        t = 0
        kill_when_done = False
        while thread.is_alive():
            time.sleep(0.5)
            t += 0.5

            updated_distance, _ = self.motors[motor_name]["motor"].get_distance_and_direction(motor_angle)
            limit = 4
            if (
                updated_distance > limit and updated_distance - last_distance > DISTANCE_TOLERANCE
            ):  # If we're moving away from the target. It's possible to overshoot the intended position by a few degrees, so don't do this check if the current position is close to the target.
                print("ERROR: NOT MAKING PROGRESS")
                if motor_name != "sample tray":
                    self.motors[motor_name]["motor"].kill_now = True
                    return {"complete": False, "position": self.motors[motor_name]["motor"].position_degrees}

            last_distance = updated_distance
        thread.join()
        return {"complete": True, "position": self.motors[motor_name]["motor"].position_degrees}

    def configure(self, i: float, e: float, tray_pos: int):
        motor_pos = self.science_pos_to_motor_pos(i, e, 0, tray_pos)  # az value is a dummy value of 0
        self.motors["incidence"]["motor"].configure(motor_pos[0][0])
        self.motors["emission"]["motor"].configure(motor_pos[1][0])
        self.motors["sample tray"]["motor"].configure(motor_pos[3][0])
        self.home_azimuth()

    def configure_incidence(self, i):
        motor_i = self.science_i_to_motor_i(i)[0]
        self.motors["incidence"]["motor"].configure(motor_i)

    def configure_emission(self, e):
        motor_e = self.science_e_to_motor_e(e)[0]
        self.motors["emission"]["motor"].configure(motor_e)

    def configure_tray(self, tray_pos):
        tray_angle = self.tray_pos_to_tray_angle(tray_pos)[0]
        self.motors["sample tray"]["motor"].configure(tray_angle)

    def home_azimuth(self, direction=motor.Motor.BACKWARD):
        if self.incidence <= -60:
            self.set_position("incidence", -60)
        self.motors["azimuth"]["motor"].home(direction)
        self.set_position("azimuth", AZIMUTH_HOME_OFFSET)
        self.motors["azimuth"]["motor"].encoder.configure(0)
        self.motors["azimuth"]["motor"].target_theta = 0
        self.motors["azimuth"]["motor"].position_full_turns = 0
        self.motors["azimuth"]["motor"].update_position(2)

    # move i, e from 20 (-70) to 160 (+70)
    # move az from 0 (0) to 170 (170)
    # move tray from 0 (WR) to 300 ('five')
    def science_pos_to_motor_pos(self, i, e, az, tray_pos):
        motor_i = self.science_i_to_motor_i(i)
        motor_e = self.science_e_to_motor_e(e)
        motor_az = self.science_az_to_motor_az(az)
        tray_angle = self.tray_pos_to_tray_angle(tray_pos)
        return motor_i, motor_e, motor_az, tray_angle

    @staticmethod
    def science_i_to_motor_i(i: float) -> Tuple[int, int]:
        return i + 90, 0  # (degrees, full turns)

    @staticmethod
    def science_e_to_motor_e(e: float) -> Tuple[int, int]:
        return e + 90, 0  # (degrees, full turns)

    def science_az_to_motor_az(self, az: float) -> Tuple[int, int]:
        # convert from science az to number of full motor turns
        total_motor_degrees = az * self.motors["azimuth"]["gear ratio"]
        turns = int(total_motor_degrees / 360)
        # motor degrees is remainder after dividing out all "full_turns" in a fraction
        # * 360 to get partial degrees of current rotation
        degrees = total_motor_degrees - turns * 360
        return degrees, turns

    @staticmethod
    def motor_i_to_science_i(i: float) -> float:
        return i - 90

    @staticmethod
    def motor_e_to_science_e(e: float) -> float:
        return e - 90

    def motor_az_to_science_az(self, turns: int, degrees: float) -> float:
        total_motor_degrees = 360 * turns + degrees
        az = total_motor_degrees / self.motors["azimuth"]["gear ratio"]
        return az

    def tray_pos_to_tray_angle(self, tray_pos: Union[str, int]) -> Tuple:
        tray_pos = str(tray_pos)
        return self.motors["sample tray"]["positions"][tray_pos], 0

    def tray_angle_to_tray_pos(self, tray_angle: int) -> str:
        for pos in self.motors["sample tray"]["positions"]:
            if self.motors["sample tray"]["positions"][pos] == tray_angle:
                return pos
        return None

    def tray_sweep(self):
        positions = ["wr", "one", "two", "three", "four", "five", "wr"]
        for pos in positions:
            self.set_position("sample tray", pos)
            time.sleep(3)

    def emission_sweep(self):
        print("Moving to 70")
        self.set_position("emission", 70)
        time.sleep(2)
        print("Moving to -70")
        self.set_position("emission", -70)
        time.sleep(2)
        for i in range(-60, 80, 10):
            print("Moving to " + str(i))
            self.set_position("emission", i)
            time.sleep(2)
        print("Moving to -70")
        self.set_position("emission", -70)
        
    def move_tray_to_nearest(self):
        smallest_diff = 360
        next_pos = 0
        current = self.tray_angle
        for val in np.arange(0, 360, 60):
            diff = np.abs(val - current)
            if diff < smallest_diff:
                smallest_diff = diff
                next_pos = val
        self.set_position("sample tray", self.tray_angle_to_tray_pos(next_pos))
        
    def update_position(self):
        for name in self.motors:
            self.motors[name]["motor"].update_position(3)
