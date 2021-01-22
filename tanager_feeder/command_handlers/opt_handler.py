from tanager_feeder.command_handlers.command_handler import CommandHandler


class OptHandler(CommandHandler):
    def __init__(self, controller, title="Optimizing...", label="Optimizing..."):

        if controller.spec_config_count != None:
            timeout_s = int(controller.spec_config_count) / 9 + 50 + BUFFER
        else:
            timeout_s = 1000
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout_s)
        self.first_try = True  # Occasionally, optimizing and white referencing may fail for reasons I haven't figured out. I made it do one automatic retry, which has yet to fail.

    def wait(self):
        while self.timeout_s > 0:
            if "nonumspectra" in self.listener.queue:
                self.listener.queue.remove("nonumspectra")
                self.controller.queue.insert(0, {self.controller.configure_instrument: []})
                self.controller.configure_instrument()
                return

            elif "noconfig" in self.listener.queue:
                self.listener.queue.remove("noconfig")
                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
                return

            elif "noconfig" in self.listener.queue:
                self.listener.queue.remove("noconfig")
                # If the next thing we're going to do is take a spectrum then set override to True - we will already have checked in with the user about those things when we first decided to take a spectrum.

                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
                return

            if "optsuccess" in self.listener.queue:
                self.listener.queue.remove("optsuccess")
                self.success()
                return

            elif "optfailure" in self.listener.queue:
                self.listener.queue.remove("optfailure")

                if (
                    self.first_try == True and not self.cancel and not self.pause
                ):  # Actually this is always true since a new OptHandler gets created for each attempt
                    self.controller.log("Error: Failed to optimize instrument. Retrying.")
                    self.first_try = False
                    self.controller.next_in_queue()
                elif self.pause:
                    self.interrupt("Error: There was a problem with\noptimizing the instrument.\n\nPaused.", retry=True)
                    self.wait_dialog.top.geometry("376x165")
                    self.controller.log("Error: There was a problem with optimizing the instrument.")
                elif not self.cancel:
                    self.interrupt("Error: There was a problem with\noptimizing the instrument.", retry=True)
                    self.wait_dialog.top.geometry("376x165")
                    self.controller.log("Error: There was a problem with optimizing the instrument.")
                else:  # You can't retry if you already clicked cancel because we already cleared out the queue
                    self.interrupt(
                        "Error: There was a problem with\noptimizing the instrument.\n\nData acquisition canceled.",
                        retry=False,
                    )
                    self.wait_dialog.top.geometry("376x165")
                    self.controller.log("Error: There was a problem with optimizing the instrument.")
                return
            time.sleep(INTERVAL)
            self.timeout_s -= INTERVAL
        self.timeout()

    def success(self):
        self.controller.opt_time = int(time.time())
        self.controller.log(
            "Instrument optimized.", write_to_file=True
        )  # \n\ti='+self.controller.active_incidence_entries[0].get()+'\n\te='+self.controller.active_emission_entries[0].get())
        super(OptHandler, self).success()
