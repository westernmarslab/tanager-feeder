import time

import numpy as np

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class GetPositionHandler(CommandHandler):
    def __init__(self, controller, title="Getting position...", label="Getting current goniometer position...", timeout=utils.PI_BUFFER):
        self.listener = controller.pi_listener
        self.i = None
        self.e = None
        self.az = None
        self.tray_pos = None
        self.success_message = "currentposition"
        super().__init__(controller, title, label, timeout)


    def wait(self):
        timeout_s = self.timeout_s
        while timeout_s > 0:
            for message in self.listener.queue:
                if self.success_message in message:
                    self.listener.queue.remove(message)
                    message = message.replace(self.success_message, "")
                    params = message.split("&")[1:]
                    self.i = int(np.round(float(params[0])))
                    self.e = int(np.round(float(params[1])))
                    self.az = int(np.round(float(params[2])))
                    try:
                        self.tray_pos = int(params[3])
                    except ValueError:
                        self.tray_pos = 0  # Needs to be updated - should require configuration.
                    self.success()
                    return

            time.sleep(utils.INTERVAL)
            timeout_s -= utils.INTERVAL

        self.timeout()

    def success(self):
        self.controller.motor_i = self.i
        self.controller.motor_e = self.e
        self.controller.motor_az = self.az
        if self.tray_pos == -1:
            self.controller.sample_tray_index = 0
        else:
            self.controller.sample_tray_index = int(self.tray_pos)
        self.interrupt("Ready to use automatic mode.")
        if self.tray_pos != -1 and self.tray_pos != 0:
            tray_position_string = self.controller.available_sample_positions[int(self.tray_pos) - 1]
        else:
            tray_position_string = "WR"

        self.controller.goniometer_view.set_azimuth(self.controller.motor_az, config=True)
        self.controller.goniometer_view.set_incidence(self.controller.motor_i, config=True)
        self.controller.goniometer_view.set_emission(self.controller.motor_e, config=True)
        self.controller.goniometer_view.set_current_sample(tray_position_string)

        self.controller.log(f"Current position:\ti = {self.i} \te = {self.e}\taz = {self.az}\ttray position: " + tray_position_string)
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
