import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class WhiteReferenceHandler(CommandHandler):
    def __init__(
        self, controller, title: str = "White referencing...", label: str = "White referencing..."):

        timeout_s: int = controller.spec_config_count / 9 + 40 + utils.BUFFER
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout_s)
        self.controller.white_referencing = True
        self.attempt = self.controller.white_reference_attempt

    def wait(self):
        while self.timeout_s > 0:
            if "wrsuccess" in self.listener.queue:
                self.listener.queue.remove("wrsuccess")
                self.success()
                return
            if "nonumspectra" in self.listener.queue:
                self.listener.queue.remove("nonumspectra")
                self.controller.queue.insert(0, {self.controller.configure_instrument: []})
                self.controller.configure_instrument()
                return
            if "noconfig" in self.listener.queue:
                self.listener.queue.remove("noconfig")
                # If the next thing we're going to do is take a spectrum then set override to True - we will already
                # have checked in with the user about those things when we first decided to take a spectrum.
                if self.controller.wr in self.controller.queue[0]:
                    self.controller.queue[0][self.controller.wr][0] = True

                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
                return
            if "wrfailed" in self.listener.queue:
                self.listener.queue.remove("wrfailed")

                if not self.cancel and not self.pause:
                    if self.attempt == 0:
                        self.controller.white_reference_attempt = 1
                        self.controller.log("Error: Failed to take white reference. Retrying.")
                    elif self.attempt == 1:
                        self.controller.white_reference_attempt = 2
                        self.controller.log(
                            "Error: Failed to take white reference. Restarting RS3 and retrying."
                        )
                        self.controller.queue.insert(0, {self.controller.restart_rs3: []})
                    elif self.attempt == 2:
                        self.controller.white_reference_attempt += 1
                        self.controller.log(
                            f"Error: Failed to take white reference. Restarting spectrometer computer and retrying."
                        )
                        self.controller.queue.insert(0, {self.controller.restart_computer: []})
                    else:
                        self.controller.white_reference_attempt += 1
                        self.controller.log(
                            f"Error: Failed to take white reference. Restarting spectrometer computer and retrying"
                            f" ({self.controller.white_reference_attempt-3})."
                        )
                        self.controller.queue.insert(0, {self.controller.restart_computer: []})
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt("Error: Failed to take white reference.\n\nPaused.", retry=True)
                    self.wait_dialog.top.geometry("376x175")
                    self.controller.log("Error: Failed to take white reference.")
                else:  # You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt("Error: Failed to take white reference.\n\nData acquisition canceled.", retry=False)
                    self.wait_dialog.top.geometry("376x175")
                    self.controller.white_reference_attempt = 0
                    # Does nothing in automatic mode
                    self.controller.clear()

                return

            if "wrfailedfileexists" in self.listener.queue:
                self.listener.queue.remove("wrfailedfileexists")

                if self.controller.overwrite_all:
                    # self.wait_dialog.top.destroy()
                    self.remove_retry(need_new=False)  # No need for new wait dialog

                elif self.controller.manual_automatic.get() == 0 and not self.controller.script_running:
                    self.interrupt("Error: File exists.\nDo you want to overwrite this data?")
                    buttons = {"yes": {self.remove_retry: []}, "no": {self.finish: []}}

                    self.wait_dialog.set_buttons(buttons)
                else:
                    self.interrupt("Error: File exists.\nDo you want to overwrite this data?")
                    buttons = {
                        "yes": {self.remove_retry: []},
                        "yes to all": {self.controller.set_overwrite_all: [True], self.remove_retry: []},
                        "no": {self.finish: []},
                    }

                    self.wait_dialog.set_buttons(buttons, button_width=10)
                self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 175, 107, 69))
                return
            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL
        # Before timing out, set override to True so that if the user decides to retry they aren't reminded about
        # optimizing, etc again.
        if len(self.controller.queue) > 0 and self.controller.wr in self.controller.queue[0]:
            self.controller.queue[0][self.controller.wr][0] = True
        self.controller.white_reference_attempt = 0
        self.timeout()

    def success(self):
        self.controller.wr_time = int(time.time())
        self.controller.white_reference_attempt = 0
        super().success()
