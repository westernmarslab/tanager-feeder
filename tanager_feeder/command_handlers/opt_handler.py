import time

from tanager_feeder.command_handlers.trigger_restart_handler import TriggerRestartHandler
from tanager_feeder import utils


class OptHandler(TriggerRestartHandler):
    def __init__(self, controller, title: str = "Optimizing...", label: str = "Optimizing..."):

        if controller.spec_config_count is not None:
            timeout_s = int(controller.spec_config_count) / 9 + 50 + utils.BUFFER
        else:
            timeout_s = 1000
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout_s)
        self.attempt = self.controller.opt_attempt

    def wait(self):
        while self.timeout_s > 0:
            if "nonumspectra" in self.listener.queue:
                self.listener.queue.remove("nonumspectra")
                self.controller.queue.insert(0, {self.controller.configure_instrument: []})
                self.controller.configure_instrument()
                return

            if "noconfig" in self.listener.queue:
                self.listener.queue.remove("noconfig")
                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
                return

            if "noconfig" in self.listener.queue:
                self.listener.queue.remove("noconfig")
                # If the next thing we're going to do is take a spectrum then set override to True - we will already
                # have checked in with the user about those things when we first decided to take a spectrum.

                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
                return

            if "optsuccess" in self.listener.queue:
                self.listener.queue.remove("optsuccess")
                self.success()
                return

            if "optfailure" in self.listener.queue:
                self.listener.queue.remove("optfailure")

                if not self.cancel and not self.pause:
                    if self.attempt == 0:
                        self.controller.opt_attempt = 1
                        self.controller.log("Error: Failed to optimize instrument. Retrying.")
                    elif self.attempt == 1:
                        self.controller.opt_attempt = 2
                        self.controller.log("Error: Failed to optimize instrument. Restarting RS3 and retrying.")
                        self.controller.queue.insert(0, {self.controller.restart_rs3: []})
                    elif self.attempt == 2:
                        self.controller.opt_attempt += 1
                        self.controller.log(
                            f"Error: Failed to optimize instrument. Restarting spectrometer computer and retrying."
                        )
                        self.controller.queue.insert(0, {self.controller.restart_computer: []})
                    else:
                        self.controller.opt_attempt += 1
                        self.controller.log(
                            f"Error: Failed to optimize instrument. Restarting spectrometer computer and retrying"
                            f" ({self.controller.opt_attempt-3})."
                        )
                        self.controller.queue.insert(0, {self.controller.restart_computer: []})
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt("Error: Failed to optimize instrument.\n\nPaused.", retry=True)
                    self.controller.opt_attempt += 1
                    self.wait_dialog.top.geometry("376x175")
                    self.controller.log("Error: Failed to optimize instrument.")
                else:  # You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt("Error: Failed to optimize instrument.\n\nData acquisition canceled.", retry=False)
                    self.wait_dialog.top.geometry("376x175")
                    self.controller.opt_attempt = 0
                return
            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.controller.opt_attempt = 0
        self.timeout()

    def success(self):
        self.controller.opt_time = int(time.time())
        self.controller.opt_attempt = 0
        self.controller.log("Instrument optimized.")
        super().success()

    def timeout(self):
        if self.cancel:
            self.controller.opt_attempt = 0
        super().timeout("optimize instrument")
