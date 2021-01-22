import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class GetPositionHandler(CommandHandler):
    def __init__(self, controller, title="Getting position...", label="Getting current goniometer position..."):
        self.listener = controller.pi_listener
        self.i = None
        self.e = None
        self.az = None
        self.tray_pos = None
        super().__init__(controller, title, label, timeout=utils.BUFFER)

    def wait(self):
        timeout_s = 2 * utils.PI_BUFFER
        while timeout_s > 0:
            for message in self.listener.queue:
                if "currentposition" in message:
                    print("laa")
                    message = message.replace("currentposition", "")
                    params = message.split("&")[1:]
                    self.i = int(float(params[0]))
                    self.e = int(float(params[1]))
                    self.az = int(float(params[2]))
                    try:
                        self.tray_pos = int(params[3])
                    except ValueError:
                        self.tray_pos = 0  # Needs to be updated - should require configuration.
                    if timeout_s <= 0:
                        self.timeout()
                    else:
                        self.success()

            time.sleep(utils.INTERVAL)
            timeout_s -= utils.INTERVAL

    def success(self):
        print(self)
        print(self.i)
        print(self.e)
        self.controller.motor_i = self.i
        self.controller.motor_e = self.e
        self.controller.motor_az = self.az
        if self.tray_pos == -1:
            self.controller.sample_tray_index = 0
        else:
            self.controller.sample_tray_index = int(self.tray_pos)

        self.interrupt("Goniometer position acquired. Ready to use automatic mode.")
        if self.tray_pos != -1 and self.tray_pos != 0:
            tray_position_string = self.controller.available_sample_positions[int(self.tray_pos) - 1]
        else:
            tray_position_string = "WR"

        self.controller.goniometer_view.set_azimuth(self.controller.motor_az, config=True)
        self.controller.goniometer_view.set_incidence(self.controller.motor_i, config=True)
        self.controller.goniometer_view.set_emission(self.controller.motor_e, config=True)
        self.controller.goniometer_view.set_current_sample(tray_position_string)

        self.log(f"Current position:\n\ti = {i} \n\te = {e}\n\taz = {az} \n\ttray position: " + tray_position_string)

        self.controller.complete_queue_item()
        if len(self.controller.queue) > 0:
            self.controller.next_in_queue()

    def timeout(self):
        super().timeout("Error: Failed to get current goniometer position.")
        self.controller.motor_i = None
        self.controller.motor_e = None
        self.controller.motor_az = None
        self.controller.set_manual_automatic(force=0)
        self.controller.unfreeze()
