import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class CloseHandler(CommandHandler):
    def __init__(
        self, controller, title: str = "Closing...", label: str = "Setting to default geometry and closing..."
    ):
        self.listener = controller.pi_listener
        super().__init__(controller, title, label, timeout=90 + utils.BUFFER)

    def wait(self):
        while self.timeout_s > 0:
            if "donemoving" in self.listener.queue:
                self.listener.queue.remove("donemoving")
                self.success()
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.timeout()

    def success(self):
        self.controller.complete_queue_item()
        if len(self.controller.queue) == 0:
            self.interrupt("Finished. Ready to exit")
            self.wait_dialog.set_buttons({"exit": {utils.exit_func: []}})
        else:
            self.controller.next_in_queue()
