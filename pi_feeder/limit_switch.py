import RPi.GPIO as GPIO


class LimitSwitch:
    def __init__(self, pin: int):
        self.pin = pin
        self.name = "Switch 2"
        if pin == 2:
            self.name = "Switch 1"
            

        # Set pins as read only
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN)
        self._keep_monitoring = False
        self.tripped = False

    # Watches for the switch to trip. If it does, sets a flag and returns.
    def monitor(self):
        self._keep_monitoring = True
        while self._keep_monitoring:
            if GPIO.input(self.pin) == GPIO.LOW:
                self.tripped = True
                return

    # Stops monitoring and resets trip flag.
    def stop_monitor(self):
        self._keep_monitoring = False
        self.tripped = False

    def get_tripped(self):
        if GPIO.input(self.pin) == GPIO.LOW:
            self.tripped = True
        else:
            self.tripped = False
        return self.tripped


class SwitchTrippedException(Exception):
    def __init__(self):
        super().__init__("Switch tripped!")
