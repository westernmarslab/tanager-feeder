import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class ListContentsHandler(CommandHandler):
    def __init__(
        self,
        controller,
        status: str,
        title: str = "Getting directory contents...",
        label: str = "Getting save directory contents...",
    ):
        self.status = status
        super().__init__(controller, title, label, timeout=3 * utils.BUFFER)

    def wait(self):
        if self.status == "listdirfailed":
            if self.controller.script_running:  # If a script is running, automatically try to make the directory.
                self.inner_mkdir(self.controller.spec_save_dir_entry.get())
            else:  # Otherwise, ask the user first.
                buttons = {
                    "yes": {self.inner_mkdir: [self.controller.spec_save_dir_entry.get()]},
                    "no": {self.controller.reset: []},
                }
                self.interrupt(
                    self.controller.spec_save_dir_entry.get()
                    + "\n\ndoes not exist. Do you want to create this directory?",
                )
                self.wait_dialog.set_buttons(buttons)
            return

        if self.status == "listdirfailedpermission":
            self.interrupt("Error: Permission denied for\n" + self.controller.spec_save_dir_entry.get(), retry=False)
            return

        if self.status == "timeout":
            self.timeout("Error: Operation timed out while listing directory contents.")
        else:
            print("here is what a success status looks like (in listcontents handler)")
            print(self.status)
            self.success()

    # inner_mkdir function gets called if the directory doesn't exist and the user clicks 'yes' for making the directory.
    def inner_mkdir(self, dir_to_make: str) -> None:
        mkdir_status = self.controller.remote_directory_worker.mkdir(dir_to_make)
        if mkdir_status == "mkdirsuccess":
            self.controller.set_save_config()
        elif mkdir_status == "mkdirfailedfileexists":
            self.interrupt("Could not create directory:\n\n" + dir_to_make + "\n\nFile exists.")
        elif mkdir_status == "mkdirfailed":
            self.interrupt("Could not create directory:\n\n" + dir_to_make)
