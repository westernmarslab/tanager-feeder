from tanager_feeder.command_handlers.command_handler import CommandHandler


class InstrumentConfigHandler(CommandHandler):
    def __init__(self, controller, title="Configuring instrument...", label="Configuring instrument...", timeout=30):
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout)

    def wait(self):
        while self.timeout_s > 0:
            if "iconfigsuccess" in self.listener.queue:
                self.listener.queue.remove("iconfigsuccess")
                self.success()
                return
            elif "iconfigfailure" in self.listener.queue:
                self.listener.queue.remove("iconfigfailure")
                self.interrupt("Error: Failed to configure instrument.", retry=True)
                self.controller.log("Error: Failed to configure instrument.")
                return

            time.sleep(INTERVAL)
            self.timeout_s -= INTERVAL
        self.timeout()

    def success(self):
        self.controller.spec_config_count = self.controller.instrument_config_entry.get()

        self.controller.log(
            "Instrument configured to average " + str(self.controller.spec_config_count) + " spectra.",
            write_to_file=True,
        )

        super(InstrumentConfigHandler, self).success()