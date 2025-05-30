import time
from typing import Optional

import numpy as np

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class GetPositionHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title: str = "Getting position...",
        label: str = "Getting current goniometer position...",
        timeout: int = utils.PI_BUFFER,
    ):
        self.listener = controller.pi_listener
        self.i: Optional[int] = None
        self.e: Optional[int] = None
        self.az: Optional[int] = None
        self.tray_pos: Optional[int] = None
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
                        self.interrupt("Error: failed to get sample tray position.")
                        self.controller.set_manual_automatic(0)
                        return
                    self.success()
                    return

            time.sleep(utils.INTERVAL)
            timeout_s -= utils.INTERVAL

        self.timeout()

    def success(self):
        self.controller.science_i = self.i
        self.controller.science_e = self.e
        self.controller.science_az = self.az
        self.controller.sample_tray_index = int(self.tray_pos)

        if self.tray_pos != -1:
            tray_position_string = self.controller.available_sample_positions[int(self.tray_pos)]
        else:
            tray_position_string = "WR"

        self.controller.goniometer_view.set_azimuth(self.controller.science_az, config=True)
        self.controller.goniometer_view.set_incidence(self.controller.science_i, config=True)
        self.controller.goniometer_view.set_emission(self.controller.science_e, config=True)
        self.controller.goniometer_view.set_current_sample(tray_position_string)

        self.controller.log(
            f"Current position:\n"
            f"\tGeometry: i = {self.i} \te = {self.e}\taz = {self.az}\n"
            f"\tTray position: {tray_position_string}\n\n"
        )

        super().success(f"Ready to use automatic mode.")

    def timeout(self):
        super().timeout("Error: Failed to get current goniometer position.")
        self.controller.science_i = None
        self.controller.science_e = None
        self.controller.science_az = None
        self.controller.set_manual_automatic(force=0)
        self.controller.unfreeze()
