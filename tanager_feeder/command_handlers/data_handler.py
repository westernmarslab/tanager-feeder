from tanager_feeder.command_handlers.command_handler import CommandHandler


class DataHandler(CommandHandler):
    def __init__(
        self,
        controller,
        title="Transferring data...",
        label="Tranferring data...",
        source=None,
        temp_destination=None,
        final_destination=None,
    ):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=2 * BUFFER)
        self.source = source
        self.temp_destination = temp_destination
        self.final_destination = final_destination
        self.wait_dialog.top.geometry("%dx%d%+d%+d" % (376, 130, 107, 69))

    def wait(self):
        while self.timeout_s > 0:
            # self.spec_commander.get_data(filename)
            if "datacopied" in self.listener.queue:
                self.listener.queue.remove("datacopied")

                if self.temp_destination != None and self.final_destination != None:
                    try:

                        shutil.move(self.temp_destination, self.final_destination)
                        # self.timeout('Error: Operation timed out while trying to transfer data.') #This is for testing
                        self.success()
                        return

                    except Exception as e:
                        print("data copied exception")
                        print(e)

                        self.interrupt("Error transferring data", retry=True)
                        return

            elif "datafailure" in self.listener.queue:
                self.listener.queue.remove("datafailure")
                self.interrupt("Error transferring data", retry=True)
                # dialog=ErrorDialog(self.controller,label='Error: Failed to acquire data.\nDoes the file exist? Do you have permission to use it?')
                return
            time.sleep(INTERVAL)
            self.timeout_s = self.timeout_s - INTERVAL
        self.timeout()

    def success(self):
        self.controller.complete_queue_item()
        self.interrupt("Data transferred successfully.")
        if len(self.controller.queue) > 0:
            self.controller.next_in_queue()
