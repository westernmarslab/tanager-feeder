import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder.connection_checkers.spec_connection_checker import SpecConnectionChecker
from tanager_feeder import utils


class RestartComputerHandler(CommandHandler):
    def __init__(
        self, controller, title: str = "Restarting...", label: str = "Restarting computer..."
    ):
        self.listener = controller.spec_listener
        self.connection_checker = SpecConnectionChecker(controller.connection_manager, controller.config_info, func=self.success)
        super().__init__(controller, title, label, timeout = 10 + utils.BUFFER)

    def wait(self):
        while self.timeout_s > 0:
            if "restarting" in self.listener.queue:
                self.listener.queue.remove("restarting")
                print("restart process begun!")
                time.sleep(30)
                t = 60
                while t > 0:
                    t -= 3
                    connected = self.connection_checker.check_connection(timeout=3, show_dialog=False)
                    if connected:
                        print("connected hooray!")
                        return
                    else:
                        print("still looking")
                        print(t)
                self.timeout()

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.timeout()

    def success(self):
        self.controller.log("Spec compy restarted.")
        time.sleep(30)
        super().success()
