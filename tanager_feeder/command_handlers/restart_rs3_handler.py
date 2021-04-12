import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class RestartRS3Handler(CommandHandler):
    def __init__(self, controller, title: str = "Restarting...", label: str = "Restarting RS3..."):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=60 * 5 + utils.BUFFER)

    def wait(self):
        while self.timeout_s > 0:
            if "rs3restarted" in self.listener.queue:
                self.listener.queue.remove("rs3restarted")
                time.sleep(90) # Give a chance for rs3 to really start
                self.success()
                return
            if "rs3restartfailed" in self.listener.queue:
                self.listener.queue.remove("rs3restartfailed")
                time.sleep(30) # Give a chance for rs3 to really start
                self.success()
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        print("RS3 restart timeout!")
        self.timeout()

    def timeout(self):
        super().timeout()
        self.controller.white_reference_attempt = 0
        self.controller.opt_attempt = 0

    def success(self):
        self.controller.white_reference_attempt = 0
        self.controller.opt_attempt = 0
        super().success()
