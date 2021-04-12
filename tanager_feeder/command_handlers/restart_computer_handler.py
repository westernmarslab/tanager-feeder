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
        super().__init__(controller, title, label, timeout=100 + utils.BUFFER)

    def wait(self):
        while True: # Once you try restarting, just keep listening.
            # Spec will keep trying to send until the message goes through.
            if "restarting" in self.listener.queue:
                print("Restarting in restart handler")
                self.controller.restarting_spec_compy = True
                self.listener.queue.remove("restarting")
                time.sleep(30)
                t = 120
                while t > 0:
                    t -= 3
                    print("trying to connect")
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

        # if self.cancel or self.pause:
        #     self.timeout()
        # else:
        #     # Automatically retry if you haven't heard that it knows to restart.
        #     # This means that even if we have to wait for the watchdog timer,
        #     # we won't give up on restarting.
        #     self.controller.log("Computer restart not registered. Retrying.")
        #     self.controller.next_in_queue()

    def timeout(self):
        #Timeout only gets called if the spec compy says it is going to restart but then it doesn't.
        self.controller.white_reference_attempt = 0
        self.controller.restarting_spec_compy = False
        super().timeout(
            retry=True, dialog_string="Error: Timed out while trying\nto restart the spectrometer computer."
        )
        self.wait_dialog.top.geometry("376x145")
        connection_checker = SpecConnectionChecker(
            self.controller.connection_manager, self.controller.config_info, func=self.pass_function
        )
        connection_checker.check_connection(timeout=3)

    def pass_function(self):
        pass

    def success(self):
        self.controller.log("Spec compy restarted. Waiting 5 minutes for reinitialization.")
        time.sleep(300) #Give time for the spectrometer to reconnect
        self.controller.restarting_spec_compy = False
        super().success()
