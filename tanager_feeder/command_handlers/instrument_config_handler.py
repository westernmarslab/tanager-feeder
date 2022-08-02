import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class InstrumentConfigHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title: str = "Configuring instrument...",
        label: str = "Configuring instrument...",
        timeout: int = 100,
    ):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout)

    def wait(self):
        while self.timeout_s > 0:
            if "iconfigsuccess" in self.listener.queue:
                self.listener.queue.remove("iconfigsuccess")
                self.success()
                return

            if "iconfigfailure" in self.listener.queue:
                self.listener.queue.remove("iconfigfailure")
                self.interrupt("Error: Failed to configure instrument.", retry=True)
                self.controller.log("Error: Failed to configure instrument.")
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL
        self.timeout()

    def success(self):
        self.controller.spec_config_count = int(self.controller.instrument_config_entry.get())
        self.controller.calfile = self.controller.target_calfile
        self.controller.log("Instrument configured.\n"
                            f"\tAveraging {self.controller.spec_config_count} spectra."
                            f"\tSpectralon calibration file: {self.controller.calfile}.")
        super().success()
