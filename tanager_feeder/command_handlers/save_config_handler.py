import time

from tkinter import END

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder.dialogs.wait_dialog import WaitDialog
from tanager_feeder import utils


class SaveConfigHandler(CommandHandler):
    def __init__(
        self, controller, title="Setting Save Configuration...", label="Setting save configuration...", timeout=30
    ):
        self.listener = controller.spec_listener
        self.keep_around = False
        self.unexpected_files = []
        self.listener.new_dialogs = False
        super().__init__(controller, title, label=label, timeout=timeout)

    def wait(self):
        t = 30
        while "donelookingforunexpected" not in self.listener.queue and t > 0:
            t = t - utils.INTERVAL
            time.sleep(utils.INTERVAL)
        if t <= 0:
            self.timeout()
            return

        if len(self.listener.unexpected_files) > 0:
            self.keep_around = True
            self.unexpected_files = list(self.listener.unexpected_files)
            self.listener.unexpected_files = []

        self.listener.new_dialogs = True
        self.listener.queue.remove("donelookingforunexpected")

        while self.timeout_s > 0:
            self.timeout_s -= utils.INTERVAL
            if "saveconfigsuccess" in self.listener.queue:

                self.listener.queue.remove("saveconfigsuccess")
                self.success()
                return

            if "saveconfigfailedfileexists" in self.listener.queue:

                self.listener.queue.remove("saveconfigfailedfileexists")
                self.interrupt("Error: File exists.\nDo you want to overwrite this data?")

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

            if "saveconfigfailed" in self.listener.queue:
                self.listener.queue.remove("saveconfigfailed")
                self.interrupt(
                    "Error: There was a problem setting the save configuration.\nIs the spectrometer connected?\n"
                    "Is the spectrometer computer awake and unlocked?",
                    retry=True,
                )
                self.controller.log("Error: There was a problem setting the save configuration.")
                self.controller.spec_save_path = ""
                self.controller.spec_basename = ""
                self.controller.spec_num = None

                return

            if "saveconfigerror" in self.listener.queue:
                self.listener.queue.remove("saveconfigerror")
                self.interrupt(
                    "Error: There was a problem setting the save configuration.\n\nIs the spectrometer connected?\n"
                    "Is the spectrometer computer awake and unlocked?",
                    retry=True,
                )
                self.controller.log("Error: There was a problem setting the save configuration.")
                self.controller.spec_save_path = ""
                self.controller.spec_basename = ""
                self.controller.spec_num = None

                return

            time.sleep(utils.INTERVAL)

        self.timeout(log_string="Error: Operation timed out while waiting to set save configuration.")

    def success(self):
        self.controller.spec_save_path = self.controller.spec_save_dir_entry.get()
        self.controller.spec_basename = self.controller.spec_basename_entry.get()
        spec_num = self.controller.spec_startnum_entry.get()
        self.controller.spec_num = int(spec_num)

        self.controller.log(
            "Save configuration set.\n\tDirectory: "
            + self.controller.spec_save_dir_entry.get()
            + "\n\tBasename: "
            + self.controller.spec_basename_entry.get()
            + "\n\tStart number: "
            + self.controller.spec_startnum_entry.get(),
            write_to_file=True,
        )

        if self.keep_around:
            dialog = WaitDialog(self.controller, title="Warning: Untracked Files", buttons={"ok": []})
            dialog.top.geometry("400x300")
            dialog.interrupt(
                "There are untracked files in the\n"
                "data directory. Do these belong here?\n\n"
                "If the directory already contains a Tanager\n"
                "log file, metadata will be appended to that file."
            )

            self.controller.log("Untracked files in data directory:\n\t" + "\n\t".join(self.unexpected_files))

            listbox = utils.ScrollableListbox(
                dialog.top,
                self.wait_dialog.bg,
                self.wait_dialog.entry_background,
                self.wait_dialog.listboxhighlightcolor,
            )
            for file in self.unexpected_files:
                listbox.insert(END, file)

            listbox.config(height=1)

        super().success()
