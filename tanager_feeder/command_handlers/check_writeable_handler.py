import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils

class CheckWriteableHandler(CommandHandler):
    def __init__(self, controller, title: str = "Checking permissions...", label: str = "Checking permissions..."):

        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=3 * utils.BUFFER)

    def wait(self):
        while self.timeout_s > 0:
            if "yeswriteable" in self.listener.queue:
                self.listener.queue.remove("yeswriteable")
                self.success()
                return
            if "notwriteable" in self.listener.queue:
                self.listener.queue.remove("notwriteable")
                self.interupt(self, label="Error: Permission denied.\nCannot write to specified directory.")
                return
            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        print("timed out while checking if writeable")
        self.timeout(
            "Error: Operation timed out while checking write permissions."
        )
