from tanager_feeder.command_handlers.command_handler import CommandHandler


class SpectrumHandler(CommandHandler):
    def __init__(self, controller, title="Saving Spectrum...", label="Saving spectrum..."):
        timeout = (
            int(controller.spec_config_count) / 8 + BUFFER
        )  # This timeout grows a little faster than the actual time to take a spectrum grows, which would be numspectra/9
        self.listener = controller.spec_listener
        super().__init__(controller, title, label, timeout=timeout)

    def wait(self):
        while self.timeout_s > 0:

            if "failedtosavefile" in self.listener.queue:
                self.listener.queue.remove("failedtosavefile")
                self.interrupt("Error: Failed to save file.\nAre you sure the spectrometer is connected?", retry=True)
                self.wait_dialog.top.wm_geometry("420x130")
                return

            elif "noconfig" in self.listener.queue:
                self.listener.queue.remove("noconfig")
                # If the next thing we're going to do is take a spectrum then set override to True - we will already have checked in with the user about those things when we first decided to take a spectrum.
                if self.controller.take_spectrum in self.controller.queue[0]:
                    self.controller.queue[0][self.controller.take_spectrum][0] = True

                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()  # self.controller.take_spectrum, [True])
                return

            elif "nonumspectra" in self.listener.queue:
                self.listener.queue.remove("nonumspectra")
                self.controller.queue.insert(0, {self.controller.configure_instrument: []})
                self.controller.configure_instrument()
                return

            elif "savedfile" in self.listener.queue:
                self.listener.queue.remove("savedfile")

                self.success()
                return
            elif "savespecfailedfileexists" in self.listener.queue:

                self.listener.queue.remove("savespecfailedfileexists")
                self.interrupt("Error: File exists.\nDo you want to overwrite this data?")
                self.wait_dialog.top.wm_geometry("420x145")

                if self.controller.overwrite_all:
                    # self.wait_dialog.top.destroy()
                    self.remove_retry(need_new=False)  # No need for a new wait_dialog

                elif self.controller.manual_automatic.get() == 0 and self.controller.script_running == False:
                    self.interrupt("Error: File exists.\nDo you want to overwrite this data?")
                    self.wait_dialog.top.wm_geometry("420x130")
                    buttons = {"yes": {self.remove_retry: []}, "no": {self.finish: []}}

                    self.wait_dialog.set_buttons(buttons)

                else:
                    self.interrupt("Error: File exists.\nDo you want to overwrite this data?")
                    self.wait_dialog.top.wm_geometry("420x130")
                    buttons = {
                        "yes": {self.remove_retry: []},
                        "yes to all": {self.controller.set_overwrite_all: [True], self.remove_retry: []},
                        "no": {self.finish: []},
                    }

                    self.wait_dialog.set_buttons(buttons, button_width=10)
                return

            time.sleep(INTERVAL)
            self.timeout_s -= INTERVAL
        dialog_string = "Error: Operation timed out while waiting to save spectrum.\n\nIf it completes later, an unexpected file could be saved to the data directory.\nThis could cause errors. Restart the software to be safe."
        log_string = "Error: Operation timed out while waiting to save spectrum.\n\tIf it completes later, an unexpected file could be saved to the data directory.\n\tThis could cause errors. Restart the software to be safe."
        self.timeout(log_string=log_string, dialog_string=dialog_string, retry=True)
        self.wait_dialog.top.wm_geometry("680x173")

    def success(self):
        self.allow_exit = True

        # Build a string that tells the number for the spectrum that was just saved. We'll use this in the log (maybe)
        lastnumstr = str(self.controller.spec_num)
        while len(lastnumstr) < NUMLEN:
            lastnumstr = "0" + lastnumstr

        # Increment the spectrum number
        self.controller.spec_num += 1
        self.controller.spec_startnum_entry.delete(0, "end")
        spec_num_string = str(self.controller.spec_num)
        while len(spec_num_string) < NUMLEN:
            spec_num_string = "0" + spec_num_string
        self.set_text(self.controller.spec_startnum_entry, spec_num_string)

        self.controller.plot_input_dir = self.controller.spec_save_dir_entry.get()

        # Use the last saved spectrum number for the log file.
        numstr = str(self.controller.spec_num - 1)
        while len(numstr) < NUMLEN:
            numstr = "0" + numstr

        # Log whether it was a white reference or a regular spectrum that just got saved.
        info_string = ""
        label = ""
        if self.controller.white_referencing:
            self.controller.white_referencing = False
            info_string = "White reference saved."
            label = "White reference"
        else:
            info_string = "Spectrum saved."
            label = self.controller.sample_label_entries[self.controller.current_sample_gui_index].get()

        info_string += (
            "\n\tSpectra averaged: "
            + str(self.controller.spec_config_count)
            + "\n\ti: "
            + str(self.controller.science_i)
            + "\n\te: "
            + str(self.controller.science_e)
            + "\n\taz: "
            + str(self.controller.science_az)
            + "\n\tfilename: "
            + self.controller.spec_save_path
            + "\\"
            + self.controller.spec_basename
            + lastnumstr
            + ".asd"
            + "\n\tLabel: "
            + label
            + "\n"
        )
        # If it was a garbage spectrum, we don't need all of the information about it. Instead, just delete it and log that it happened.
        if "garbage" in self.wait_dialog.label:

            self.controller.spec_commander.delete_spec(
                self.controller.spec_save_path, self.controller.spec_basename, lastnumstr
            )

            t = BUFFER
            while t > 0:
                if "rmsuccess" in self.listener.queue:
                    self.listener.queue.remove("rmsuccess")
                    self.controller.log(
                        "\nSaved and deleted a garbage spectrum ("
                        + self.controller.spec_basename
                        + lastnumstr
                        + ".asd)."
                    )
                    break
                elif "rmfailure" in self.listener.queue:
                    self.listener.queue.remove("rmfailure")
                    self.controller.log(
                        "\nError: Failed to remove placeholder spectrum ("
                        + self.controller.spec_basename
                        + lastnumstr
                        + ".asd. This data is likely garbage. "
                    )
                    break
                t = t - INTERVAL
                time.sleep(INTERVAL)
            if t <= 0:
                self.controller.log(
                    "\nError: Operation timed out removing placeholder spectrum ("
                    + self.controller.spec_basename
                    + lastnumstr
                    + ".asd). This data is likely garbage."
                )
        else:
            self.controller.log(info_string, True)

        self.controller.clear()
        super(SpectrumHandler, self).success()
