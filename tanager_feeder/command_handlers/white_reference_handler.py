import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils



class WhiteReferenceHandler(CommandHandler):
    def __init__(self, controller, title="White referencing...", label="White referencing..."):

        timeout_s = int(controller.spec_config_count) / 9 + 40 + utils.BUFFER
        self.listener = controller.spec_listener
        self.first_try = True
        super().__init__(controller, title, label, timeout=timeout_s)
        self.controller.white_referencing = True

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

                if (
                    self.first_try and not self.cancel
                ):  # Actually this is always true since a new OptHandler gets created for each attempt
                    self.controller.log("Error: Failed to take white reference. Retrying.")
                    self.first_try = False
                    time.sleep(15)  # Might improve the odds that the second attempt will succeed (not sure).
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt("Error: Failed to take white reference.\n\nPaused.", retry=True)
                    self.wait_dialog.top.geometry("376x175")
                    self.controller.log("Error: Failed to take white reference.")
                elif not self.cancel:
                    self.interrupt("Error: Failed to take white reference.", retry=True)
                    self.set_text(
                        self.controller.sample_label_entries[self.controller.current_sample_gui_index],
                        self.controller.current_label,
                    )
                else:  # You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt("Error: Failed to take white reference.\n\nData acquisition canceled.", retry=False)
                    self.wait_dialog.top.geometry("376x175")
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
        if self.controller.wr in self.controller.queue[0]:
            self.controller.queue[0][self.controller.wr][0] = True
        self.timeout()

    def success(self):
        self.controller.wr_time = int(time.time())
        super().success()
