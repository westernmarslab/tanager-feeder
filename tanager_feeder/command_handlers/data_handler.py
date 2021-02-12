import time
from typing import Optional

import shutil

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class DataHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title: str = "Transferring data...",
        label: str = "Tranferring data...",
        source: Optional[str] = None,
        temp_destination: Optional[str] = None,
        final_destination: Optional[str] = None,
    ):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=2 * utils.BUFFER)
        self.source = source
        self.temp_destination = temp_destination
        self.final_destination = final_destination
        self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))

    def wait(self):
        while self.timeout_s > 0:
            if "datacopied" in self.listener.queue:
                self.listener.queue.remove("datacopied")

                if self.temp_destination is not None and self.final_destination is not None:
                    try:
                        shutil.move(self.temp_destination, self.final_destination)
                    # pylint: disable = broad-except
                    except Exception as e:
                        print("Exception moving data")
                        print(e)
                        self.interrupt("Error transferring data", retry=True)
                        return

                    self.success()
                    return

            elif "datafailure" in self.listener.queue:
                self.listener.queue.remove("datafailure")
                self.interrupt("Error transferring data", retry=True)
                return
            time.sleep(utils.INTERVAL)
            self.timeout_s = self.timeout_s - utils.INTERVAL
        self.timeout()

    def success(self):
        self.controller.complete_queue_item()
        self.interrupt("Data transferred successfully.")
        if len(self.controller.queue) > 0:
            self.controller.next_in_queue()
