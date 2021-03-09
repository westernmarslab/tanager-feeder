import time
from typing import Optional

from tanager_feeder.command_handlers.command_handler import CommandHandler
from tanager_feeder import utils


class DataHandler(CommandHandler):
    def __init__(
        self,
        controller,
        destination: str,
        title: str = "Transferring data...",
        label: str = "Tranferring data...",
    ):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=2 * utils.BUFFER)
        self.destination = destination
        self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))
        self.controller.log("Tranferring data...", newline=False)

    def wait(self):
        data=[]
        next_batch = 0
        while self.timeout_s > 0:
            batch_string = f"batch{next_batch}"
            for item in self.listener.queue:
                if f"datatransferstarted" in item:
                    total_batches = float(item.replace("datatransferstarted",""))
                if batch_string in item:
                    self.listener.queue.remove(item)
                    if next_batch +1 < total_batches:
                        percent_complete = int((next_batch+1)/total_batches*100)
                        self.controller.log(f" {percent_complete}%", newline=False)
                    else:
                        percent_complete = 100
                        self.controller.log(f" {percent_complete}%", newline=True)

                    data.append(item[len(batch_string):])
                    next_batch += 1
                    self.timeout_s = 2*utils.BUFFER

            if f"datatransfercomplete{next_batch}" in self.listener.queue:
                self.listener.queue.remove(f"datatransfercomplete{next_batch}")
                self.controller.log("\n\n", newline=False)
                try:
                    with open(self.destination, "w+") as file:
                        for batch in data:
                            file.write(batch)
                except OSError:
                    print("Exception writing data")
                    self.interrupt(f"Error writing data to control computer location.\nDo you have permission to write to\n{self.destination}?", retry=True)
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
        self.interrupt("Data transferred successfully.")
        super().success()

