import time

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
        data = []
        next_batch = 0
        while self.timeout_s > 0:
            batch_string = f"batch{next_batch}+"
            for item in self.listener.queue:
                if type(item) == dict:
                    print(item.keys())
                else:
                    print(item[0:20])
            print(batch_string)
            for item in self.listener.queue:
                if f"datatransferstarted" in item:
                    total_batches = float(item.replace("datatransferstarted", ""))
                if batch_string in item:
                    if next_batch + 1 < total_batches:
                        percent_complete = int((next_batch + 1) / total_batches * 100)
                        self.controller.log(f" {percent_complete}%", newline=False)
                    else:
                        percent_complete = 100
                        self.controller.log(f" {percent_complete}%", newline=True)

                    print(item[0:40])
                    data.append(item[len(batch_string):])
                    next_batch += 1
                    batch_string = f"batch{next_batch}+"
                    self.timeout_s = 2 * utils.BUFFER

            if f"datatransfercomplete{next_batch}" in self.listener.queue:

                self.listener.queue.remove(f"datatransfercomplete{next_batch}")
                self.listener.queue = []
                self.controller.log("\n\n", newline=False)
                try:
                    with open(self.destination, "w+") as file:
                        for batch in data:
                            print(batch[0:10])
                            file.write(batch)
                except OSError:
                    print("Exception writing data")
                    self.interrupt(
                        f"Error writing data to control computer location.\nDo you have permission to write to\n{self.destination}?",
                        retry=True,
                    )
                    self.wait_dialog.top.wm_geometry("376x175")
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
