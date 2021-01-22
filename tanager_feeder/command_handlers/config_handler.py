import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class ConfigHandler(CommandHandler):
    def __init__(self, controller, title="Configuring Pi...", label="Configuring Pi...", timeout=utils.PI_BUFFER + 30):
        self.listener = controller.pi_listener
        super().__init__(controller, title, label, timeout=timeout)
        self.config_i = None
        self.config_e = None
        self.config_az = None
        self.config_tray_pos = None

    def wait(self):
        timeout_s = utils.PI_BUFFER
        while timeout_s > 0:
            for message in self.listener.queue:
                if "piconfigsuccess" in message:
                    message = message.replace("piconfigsuccess", "")
                    params = message.split("&")[1:]
                    print(params)
                    self.config_i = int(float(params[0]))
                    self.config_e = int(float(params[1]))
                    self.config_az = int(float(params[2]))
                    self.config_tray_pos = int(float(params[3]))
                break

            time.sleep(utils.INTERVAL)
            timeout_s -= utils.INTERVAL

        if timeout_s <= 0:
            self.timeout()
        else:
            self.success()

    def success(self):
        self.controller.motor_i = self.config_i
        self.controller.motor_e = self.config_e
        self.controller.motor_az = self.config_az
        if self.config_tray_pos == -1:
            self.controller.sample_tray_index = 0
        else:
            self.controller.sample_tray_index = int(self.config_tray_pos)

        self.interrupt("Goniometer configured successfully.")
        if self.config_tray_pos != -1 and self.config_tray_pos != 0:
            tray_position_string = self.controller.available_sample_positions[int(self.config_tray_pos) - 1]
        else:
            tray_position_string = "WR"

        self.controller.goniometer_view.set_azimuth(self.motor_az, config=True)
        self.controller.goniometer_view.set_incidence(self.motor_i, config=True)
        self.controller.goniometer_view.set_emission(self.motor_e, config=True)
        self.controller.goniometer_view.set_current_sample(tray_position_string)

        self.log(
            f"Raspberry pi configured.\n\ti = {i} \n\te = {e}\n\taz = {az} \n\ttray position: " + tray_position_string
        )

        self.controller.complete_queue_item()
        if len(self.controller.queue) > 0:
            self.controller.next_in_queue()

    def timeout(self):
        super().timeout("Error: Failed to configure Raspberry Pi.")
        self.controller.motor_i = None
        self.controller.motor_e = None
        self.controller.motor_az = None
        self.controller.set_manual_automatic(force=0)
        self.controller.unfreeze()
