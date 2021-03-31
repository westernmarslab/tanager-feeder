import time

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder.connection_checkers.spec_connection_checker import SpecConnectionChecker
from tanager_feeder import utils


class RestartComputerHandler(CommandHandler):
    def __init__(self, controller, title: str = "Restarting...", label: str = "Restarting computer..."):
        self.listener = controller.spec_listener
        self.connection_checker = SpecConnectionChecker(
            controller.connection_manager, controller.config_info, func=self.success
        )
        super().__init__(controller, title, label, timeout=10 + utils.BUFFER)

    def wait(self):
        while self.timeout_s > 0:
            if "restarting" in self.listener.queue:
                self.listener.queue.remove("restarting")
                time.sleep(30)
                t = 120
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
                return

            time.sleep(utils.INTERVAL)
            self.timeout_s -= utils.INTERVAL

        self.timeout()

    def timeout(self):
        self.controller.white_reference_attempt = 0
        super().timeout(
            retry=False, dialog_string="Error: Timed out while trying\nto restart the spectrometer computer."
        )
        self.wait_dialog.top.geometry("376x145")
        connection_checker = SpecConnectionChecker(
            self.controller.connection_manager, self.controller.config_info, func=self.pass_function
        )
        connection_checker.check_connection(timeout=3)

    def pass_function(self):
        pass

    def success(self):
        self.controller.log("Spec compy restarted.")
        time.sleep(30)
        super().success()
