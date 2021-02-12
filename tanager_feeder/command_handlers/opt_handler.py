import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class OptHandler(CommandHandler):
    def __init__(self, controller, title="Optimizing...", label="Optimizing..."):

        if controller.spec_config_count is not None:
            timeout_s = int(controller.spec_config_count) / 9 + 50 + utils.BUFFER
        else:
            timeout_s = 1000
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout_s)

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

                if (
                    not self.cancel and not self.pause
                ):
                    self.controller.log("Error: Failed to optimize instrument. Retrying.")
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt("Error: There was a problem with\noptimizing the instrument.\n\nPaused.", retry=True)
                    self.wait_dialog.top.geometry("376x165")
                    self.controller.log("Error: There was a problem with optimizing the instrument.")
                elif not self.cancel:
                    self.interrupt("Error: There was a problem with\noptimizing the instrument.", retry=True)
                    self.wait_dialog.top.geometry("376x165")
                    self.controller.log("Error: There was a problem with optimizing the instrument.")
                else:  # You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt(
                        "Error: There was a problem with\noptimizing the instrument.\n\nData acquisition canceled.",
                        retry=False,
                    )
                    self.wait_dialog.top.geometry("376x165")
                    self.controller.log("Error: There was a problem with optimizing the instrument.")
                return
            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL
        self.timeout()

    def success(self):
        self.controller.opt_time = int(time.time())
        self.controller.log(
            "Instrument optimized.", write_to_file=True
        )
        super().success()
