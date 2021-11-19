from threading import Thread
import time
from typing import List

import numpy as np
import RPi.GPIO as GPIO

from pi_feeder.limit_switch import SwitchTrippedException

MAX_NUM_STEPS = 50000
GPIO.setwarnings(False)
BREAK_TIME = 0

class Motor:
    BACKWARD = "backward"
    FORWARD = "forward"

    def __init__(
        self,
        name: str,
        pins: List[int],
        limit_sws,
        steps_per_degree: float,
        delay: float,
        encoder,
        gear_ratio: float = 1,
        wrap_around=False,
    ):
        self.name = name
        self.pins = pins
        for pin in self.pins:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)

        self.limit_sws = limit_sws
        self.steps_per_degree = steps_per_degree
        self.delay = delay
        self.encoder = encoder
        # motor_gear_ratio is max num rotations
        self.motor_gear_ratio = gear_ratio
        self.wrap_around = wrap_around

        self.kill_now = False  # Referenced during movements to see if the goniometer wants the motor to stop.
        self.position_full_turns = None
        self._position_degrees = None
        # For azimuth motor, can have problems if rotational position is zero degrees
        # because encoder may read e.g. 359.9. Solve this by checking against target_theta.
        self.target_theta = self.encoder.get_position_degrees()
        self.update_position()

    @property
    def position_degrees(self):
        return self._position_degrees

    @position_degrees.setter
    def position_degrees(self, theta):
        if theta is None:
            self._position_degrees = theta
        else:
            if self.target_theta < 60 and theta > 300:
                self._position_degrees = theta - 360
            elif self.target_theta > 300 and theta < 60:
                self._position_degrees = theta + 360
            else:
                self._position_degrees = float(theta)

    def set_full_turns(self, target_turns):
        self.target_theta = self.position_degrees # Should finish at same angle as started
        turns_needed = np.abs(target_turns - self.position_full_turns)

        if turns_needed == 0:
            return
        steps_needed = int(turns_needed * 360 * self.steps_per_degree)
        if target_turns > self.position_full_turns:
            self.forward(steps_needed)
        else:
            self.backward(steps_needed)
        self.update_position(1)

        self.position_full_turns = target_turns

    def move_to_angle(self, target_theta: int):
        tries = 50

        self.target_theta = target_theta
        while abs(self.position_degrees - target_theta) > 3 / self.steps_per_degree and tries > 0 and not self.kill_now:
            distance, sign = self.get_distance_and_direction(target_theta)
            numsteps = int(sign * distance * self.steps_per_degree)

            if numsteps == 0:
                return "success"
            tries -= 1
            self.move_steps(numsteps)
            self.update_position(5)

        if tries == 0:
            return "timeout"
        elif self.kill_now:
            return "killed"
        else:
            return "success"

    # JK made homing routine here
    def home(self, direction):
        # JK homing can be forwards or backwards: I chose backwards
        # if particular motor has limit switches, and fully backward triggers
        # a limit switch, zero the encoder angle and turn counts
        if direction == self.BACKWARD:
            try:
                self.backward(MAX_NUM_STEPS)
            except SwitchTrippedException:
                pass
        elif direction == self.FORWARD:
            try:
                self.forward(MAX_NUM_STEPS)
            except SwitchTrippedException:
                pass
        else:
            raise Exception("Invalid direction")
        self.encoder.configure(0)
        self.target_theta = 0
        self.position_full_turns = 0
        self.update_position(5)

    def move_toward_angle(self, target_theta, increment):
        distance, sign = self.get_distance_and_direction(target_theta)
        numsteps = int(sign * increment * self.steps_per_degree)
        self.move_steps(numsteps)

    def move_steps(self, numsteps: int):
        if numsteps > 0:
            func = self.forward
        else:
            func = self.backward
        numsteps = abs(numsteps)
        thread = Thread(target=func, args=(numsteps,))
        thread.start()

        while thread.is_alive():
            time.sleep(0.2)
            self.update_position()

    def get_distance_and_direction(self, target_theta):
        if self.wrap_around: # Azimuth only
            if target_theta < self.position_degrees:  # e.g. at 300, want to reach 0
                forward_distance = (360 - self.position_degrees) + target_theta  # e.g. 60 for 0, 70 for 10
                backward_distance = self.position_degrees - target_theta
            else:  # e.g. at 0, want to reach 300
                forward_distance = target_theta - self.position_degrees
                backward_distance = (
                    360 - target_theta
                ) + self.position_degrees  # e.g. 60 for current pos = zero, 70 for 10
            if forward_distance < backward_distance:
                # Move forward
                return forward_distance, 1
            else:
                return backward_distance, -1
        else:
            if self.position_degrees > target_theta:
                return self.position_degrees - target_theta, -1
            else:
                return target_theta - self.position_degrees, 1

    # JK updated to account for multiple turns as measured by encoder.
    # Get the angular measurement as read by encoder, / by gear ratio.
    # This returns fractions of degrees used by encoder.
    # Add number of rotations as fractions of the number of rotations "turns"/
    # gear ratio * 360 degrees.
    def update_position(self, num_measurements=5):
        self.position_degrees = self.encoder.get_position_degrees(num_measurements)

    def forward(self, steps, monitor=True):
        for i in range(0, steps):
            if self.kill_now:
                break
            elif monitor:
                for switch in self.limit_sws:
                    if switch.get_tripped():
                        self.backward(10, False)
                        raise SwitchTrippedException()
                        return

            if i < steps - 15:
                self.set_step(1, 0)
                time.sleep(self.delay)
                self.set_step(0, 0)
                time.sleep(self.delay)
            else:
                delay_scaling_factor = 6/np.sqrt(steps - i)
                self.set_step(1, 0)
                time.sleep(delay_scaling_factor*self.delay)
                self.set_step(0, 0)
                time.sleep(delay_scaling_factor*self.delay)

    def backward(self, steps, monitor=True):
        for i in range(0, steps):
            if self.kill_now:
                break
            elif monitor:
                for switch in self.limit_sws:
                    if switch.get_tripped():
                        self.forward(10, False)
                        raise SwitchTrippedException()
                        return
            if i < steps - 30:
                self.set_step(1, 1)
                time.sleep(self.delay)
                self.set_step(0, 1)
                time.sleep(self.delay)
            else:
                delay_scaling_factor = 6/np.sqrt(steps - i)
                self.set_step(1, 1)
                time.sleep(delay_scaling_factor*self.delay)
                self.set_step(0, 1)
                time.sleep(delay_scaling_factor*self.delay)

    def set_step(self, w1, w2):
        GPIO.output(self.pins[0], w1)
        GPIO.output(self.pins[1], w2)

    def configure(self, current_position):
        self.encoder.configure(current_position)
        self.update_position(10)
