import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class CalfileConfigHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title: str = "Setting Spectralon calibration file...",
        label: str = "Setting Spectralon calibration file...",
        timeout: int = 30,
    ):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout)

    def wait(self):
        while self.timeout_s > 0:
            if "calfileconfigsuccess" in self.listener.queue:
                self.listener.queue.remove("calfileconfigsuccess")
                self.success()
                return

            if "calfileconfigfailure" in self.listener.queue:
                self.listener.queue.remove("calfileconfigfailure")
                self.interrupt("Error: Failed to set calibration file.", retry=True)
                self.controller.log("Error: Failed to set Spectralon calibration file.")
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL
        self.timeout()

    def success(self):

        super().success()
