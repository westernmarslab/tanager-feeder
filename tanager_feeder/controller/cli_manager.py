import time
from tkinter import END

from tanager_feeder import utils

# pylint: disable = bare-except, broad-except


class CliManager:
    def __init__(self, controller):
        self.controller = controller

    def execute_cmd(
        self, cmd
    ):  # In a separate method because that allows it to be spun off in a new thread, so tkinter mainloop continues,
        # which means that the console log gets updated immediately e.g. if you say sleep(10) it will say sleep up in
        # the log while it is sleeping.
        print("Command is: " + cmd)

        def get_val(param):
            return param.split("=")[1].strip(" ").strip('"').strip("'")

        if cmd == "wr()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.wr: [True, False]})
            self.controller.queue.insert(1, {self.controller.take_spectrum: [True, True, False]})
            self.controller.wr(True, False)
        elif cmd == "opt()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.opt: [True, False]})
            self.controller.opt(True, False)  # override=True, setup complete=False
        elif cmd == "goniometer.configure(MANUAL)":
            self.controller.set_manual_automatic(force=0)

        elif "goniometer.configure(" in cmd:
            try:
                if "AUTOMATIC" in cmd:
                    # e.g. goniometer.configure(AUTOMATIC,-30,50,wr)
                    params = cmd[0:-1].split("goniometer.configure(AUTOMATIC")[1].split(",")[1:]
                    for i, param in enumerate(params):
                        params[i] = param.strip(" ")
                elif "MANUAL" in cmd:
                    params = cmd[0:-1].split("goniometer.configure(MANUAL")[1].split(",")[1:]
                    params.append(1)
                else:
                    self.controller.log(
                        "Error: invalid arguments for mode, i, e, az, sample_num: "
                        + str(cmd.replace("goniometer.configure(", "")[:-1])
                        + "\nExample input: goniometer.configure(AUTOMATIC, 0, 20, wr)"
                    )
                    self.controller.queue = []
                    self.controller.script_running = False

                valid_i = utils.validate_int_input(params[0], self.controller.min_motor_i, self.controller.max_motor_i)
                valid_e = utils.validate_int_input(params[1], self.controller.min_motor_e, self.controller.max_motor_e)
                valid_az = utils.validate_int_input(
                    params[2], self.controller.min_motor_az, self.controller.max_motor_az
                )

                valid_sample = utils.validate_int_input(params[2], 1, int(self.controller.num_samples))
                if params[2] == "wr":
                    valid_sample = True
                if valid_i and valid_e and valid_az and valid_sample:
                    self.controller.motor_i = params[0]
                    self.controller.motor_e = params[1]
                    self.controller.motor_az = params[2]

                    if params[3] == "wr":
                        self.controller.sample_tray_index = -1
                    else:
                        self.controller.sample_tray_index = (
                            int(params[3]) - 1
                        )  # this is used as an index where available_sample_positions[4]=='Sample 5' so it should be
                        # one less than input.

                    if "AUTOMATIC" in cmd:
                        self.controller.set_manual_automatic(force=1, known_goniometer_state=True)
                    else:
                        self.controller.set_manual_automatic(force=0)
                    self.controller.incidence_entries[0].delete(0, "end")
                    self.controller.incidence_entries[0].insert(0, params[0])
                    self.controller.emission_entries[0].delete(0, "end")
                    self.controller.emission_entries[0].insert(0, params[1])
                    self.controller.azimuth_entries[0].insert(0, params[2])
                    self.controller.configure_pi(params[0], params[1], params[2], params[3], params[4])

                else:
                    self.controller.log(
                        "Error: invalid arguments for mode, i, e, az, sample_num: "
                        + str(params)
                        + "\nExample input: goniometer.configure(AUTOMATIC, 0, 20, 90, wr)"
                    )
                    self.controller.queue = []
                    self.controller.script_running = False

            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
        elif cmd == "collect_garbage()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.take_spectrum: [True, False, True]})
            self.controller.take_spectrum(True, False, True)
        elif cmd == "acquire()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.acquire()
        elif cmd == "take_spectrum()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.take_spectrum: [True, True, False]})
            self.controller.take_spectrum(True, True, False)
        # e.g. set_spec_save(directory=R:\RiceData\Kathleen\test_11_15, basename=test,num=0000)
        elif "setup_geom(" in cmd:  # params are i, e, index=0
            params = cmd[0:-1].split("setup_geom(")[1].split(",")
            if len(params) != 2 and len(params) != 3:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
            elif self.controller.manual_automatic.get() == 0:  # manual mode
                valid_i = utils.validate_int_input(params[0], self.controller.min_motor_i, self.controller.max_motor_i)
                valid_e = utils.validate_int_input(params[1], self.controller.min_motor_i, self.controller.max_motor_i)
                valid_az = utils.validate_int_input(
                    params[2], self.controller.min_motor_az, self.controller.max_motor_az
                )
                if not valid_i or not valid_e or not valid_az:
                    self.controller.log(
                        "Error: i="
                        + params[0]
                        + ", e="
                        + params[1]
                        + ", az="
                        + params[2]
                        + " is not a valid viewing geometry."
                    )
                else:
                    self.controller.incidence_entries[0].delete(0, "end")
                    self.controller.incidence_entries[0].insert(0, params[0])
                    self.controller.emission_entries[0].delete(0, "end")
                    self.controller.emission_entries[0].insert(0, params[1])
                    self.controller.azimuth_entries[0].delete(0, "end")
                    self.controller.azimuth_entries[0].insert(0, params[2])
            else:  # automatic mode
                valid_i = utils.validate_int_input(params[0], self.controller.min_motor_i, self.controller.max_motor_i)
                valid_e = utils.validate_int_input(params[1], self.controller.min_motor_e, self.controller.max_motor_e)
                valid_az = utils.validate_int_input(
                    params[2], self.controller.min_motor_az, self.controller.max_motor_az
                )

                if not valid_i or not valid_e or not valid_az:
                    self.controller.log(
                        "Error: i="
                        + params[0]
                        + ", e="
                        + params[1]
                        + ", az="
                        + params[1]
                        + " is not a valid viewing geometry."
                    )
                else:
                    index = 0
                    if len(params) == 3:
                        index = int(get_val(params[2]))
                    valid_index = utils.validate_int_input(index, 0, len(self.controller.emission_entries) - 1)
                    if not valid_index:
                        self.controller.log(
                            "Error: "
                            + str(index)
                            + " is not a valid index. Enter a value from 0-"
                            + str(len(self.controller.emission_entries) - 1)
                        )
                    else:
                        self.controller.incidence_entries[index].delete(0, "end")
                        self.controller.incidence_entries[index].insert(0, params[0])
                        self.controller.emission_entries[index].delete(0, "end")
                        self.controller.emission_entries[index].insert(0, params[1])
                        self.controller.azimuth_entires[index].delete(0, "end")
                        self.controller.azimuth_entries[index].insert(0, params[2])
        elif "add_geom(" in cmd:  # params are i, e. Will not overwrite existing geom.
            params = cmd[0:-1].split("add_geom(")[1].split(",")
            if len(params) != 2:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
            elif self.controller.manual_automatic.get() == 0:  # manual mode
                valid_i = utils.validate_int_input(
                    params[0], self.controller.min_science_i, self.controller.max_science_i
                )
                valid_e = utils.validate_int_input(
                    params[1], self.controller.min_science_e, self.controller.max_science_e
                )
                valid_az = utils.validate_int_input(
                    params[2], self.controller.min_science_az, self.controller.max_science_az
                )

                if not valid_i or not valid_e or not valid_az:
                    self.controller.log(
                        "Error: i="
                        + params[0]
                        + ", e="
                        + params[1]
                        + ", az="
                        + params[2]
                        + " is not a valid viewing geometry."
                    )
                elif (
                    self.controller.emission_entries[0].get() == ""
                    and self.controller.incidence_entries[0].get() == ""
                    and self.controller.azimuth_entries[0].get() == ""
                ):
                    self.controller.incidence_entries[0].insert(0, params[0])
                    self.controller.emission_entries[0].insert(0, params[1])
                    self.controller.azimuth_entries[0].insert(0, params[2])
                else:
                    self.controller.log("Error: Cannot add second geometry in manual mode.")
            else:  # automatic mode
                if self.controller.individual_range.get() == 1:
                    self.controller.log("Error: Cannot add geometry in range mode. Use setup_geom_range() instead")
                else:
                    valid_i = utils.validate_int_input(
                        params[0], self.controller.min_science_i, self.controller.max_science_i
                    )
                    valid_e = utils.validate_int_input(
                        params[1], self.controller.min_science_e, self.controller.max_science_e
                    )
                    valid_az = utils.validate_int_input(
                        params[2], self.controller.min_science_az, self.controller.max_science_az
                    )

                    if not valid_i or not valid_e or not valid_az:
                        self.controller.log(
                            "Error: i="
                            + params[0]
                            + ", e="
                            + params[1]
                            + ", az="
                            + params[2]
                            + " is not a valid viewing geometry."
                        )
                    elif (
                        self.controller.emission_entries[0].get() == ""
                        and self.controller.incidence_entries[0].get() == ""
                    ):
                        self.controller.incidence_entries[0].insert(0, params[0])
                        self.controller.emission_entries[0].insert(0, params[1])
                        self.controller.azimuth_entries[0].insert(0, params[2])
                    else:
                        self.controller.add_geometry()
                        self.controller.incidence_entries[-1].insert(0, params[0])
                        self.controller.emission_entries[-1].insert(0, params[1])
                        self.controller.azimuth_entries[-1].insert(0, params[2])

        elif "setup_geom_range(" in cmd:
            if self.controller.manual_automatic.get() == 0:
                self.controller.log("Error: Not in automatic mode")
                self.controller.queue = []
                self.controller.script_running = False
                return False
            self.controller.set_individual_range(force=1)
            params = cmd[0:-1].split("setup_geom_range(")[1].split(",")
            for param in params:
                if "i_start" in param:
                    try:
                        self.controller.light_start_entry.delete(0, "end")
                        self.controller.light_start_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse initial incidence angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "i_end" in param:
                    try:
                        self.controller.light_end_entry.delete(0, "end")
                        self.controller.light_end_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse final incidence angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "e_start" in param:
                    try:
                        self.controller.detector_start_entry.delete(0, "end")
                        self.controller.detector_start_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse initial emission angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "e_end" in param:
                    try:
                        self.controller.detector_end_entry.delete(0, "end")
                        self.controller.detector_end_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse final emission angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "az_start" in param:
                    try:
                        self.controller.azimuth_start_entry.delete(0, "end")
                        self.controller.azimuth_start_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse initial azimuth angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "az_end" in param:
                    try:
                        self.controller.azimuth_end_entry.delete(0, "end")
                        self.controller.azimuth_end_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse final azimuth angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "i_increment" in param:
                    try:
                        self.controller.light_increment_entry.delete(0, "end")
                        self.controller.light_increment_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse incidence angle increment.")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "e_increment" in param:
                    try:
                        self.controller.detector_increment_entry.delete(0, "end")
                        self.controller.detector_increment_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse emission angle increment.")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "az_increment" in param:
                    try:
                        self.controller.azimuth_increment_entry.delete(0, "end")
                        self.controller.azimuth_increment_entry.insert(0, get_val(param))
                    except:
                        self.controller.log("Error: Unable to parse azimuth angle increment.")
                        self.controller.queue = []
                        self.controller.script_running = False
            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()
        elif "set_samples(" in cmd:
            params = cmd[0:-1].split("set_samples(")[1].split(",")
            if params == [""]:
                params = []

            # First clear all existing sample names
            while len(self.controller.sample_frames) > 1:
                self.controller.remove_sample(-1)
            self.controller.set_text(self.controller.sample_label_entries[0], "")

            # Then add in samples in order specified in params. Each param should be a sample name and pos.
            skip_count = 0  # If a param is badly formatted, we'll skip it. Keep track of how many are skipped in order
            # to index labels, etc right.
            for i, param in enumerate(params):

                try:
                    pos = param.split("=")[0].strip(" ")
                    name = get_val(param)
                    valid_pos = utils.validate_int_input(pos, 1, 5)
                    if (
                        self.controller.available_sample_positions[int(pos) - 1]
                        in self.controller.taken_sample_positions
                    ):  # If the requested position is already taken, we're not going to allow it.
                        if (
                            len(self.controller.sample_label_entries) > 1
                        ):  # If only one label is out there, it will be listed as taken even though the entry is empty,
                            # so we can ignore it. But if there is more than one label, we know the position is a repeat
                            # and not valid.
                            valid_pos = False
                        elif (
                            self.controller.sample_label_entries[0].get() != ""
                        ):  # Even if there is only one label, if the entry has already been filled in then the position
                            # is a repeat and not valid.
                            valid_pos = False
                    if i - skip_count != 0 and valid_pos:
                        self.controller.add_sample()
                except:  # If the position isn't specified, fail.
                    self.controller.log(
                        "Error: could not parse command "
                        + cmd
                        + ". Use the format set_samples({position}={name}) e.g. set_samples(1=Basalt)"
                    )
                    skip_count += 1

                if valid_pos:
                    self.controller.set_text(self.controller.sample_label_entries[i - skip_count], name)
                    self.controller.sample_pos_vars[i - skip_count].set(
                        self.controller.available_sample_positions[int(pos) - 1]
                    )
                    self.controller.set_taken_sample_positions()
                else:
                    self.controller.log(
                        "Error: " + pos + " is an invalid sample position. Use the format set_samples({position}={1}) "
                        "e.g. set_samples(1=Basalt). Do not repeat sample positions."
                    )
                    skip_count += 1

            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()

        elif "set_spec_save(" in cmd:
            self.controller.unfreeze()
            params = cmd[0:-1].split("set_spec_save(")[1].split(",")

            for i, param in enumerate(params):
                params[i] = param.strip(" ")  # Need to do this before looking for setup only
                if "directory" in param:
                    save_dir = get_val(param)
                    self.controller.spec_save_dir_entry.delete(0, "end")
                    self.controller.spec_save_dir_entry.insert(0, save_dir)
                elif "basename" in param:
                    basename = get_val(param)
                    self.controller.spec_basename_entry.delete(0, "end")
                    self.controller.spec_basename_entry.insert(0, basename)
                elif "num" in param:
                    num = get_val(param)
                    self.controller.spec_startnum_entry.delete(0, "end")
                    self.controller.spec_startnum_entry.insert(0, num)

            if not self.controller.script_running:
                self.controller.queue = []

            # If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI is
            # just filled in for them how they want.
            setup_only = False

            if "setup_only=True" in params:
                setup_only = True
            elif "setup_only =True" in params:
                setup_only = True
            elif "setup_only = True" in params:
                setup_only = True

            if not setup_only:
                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
            elif len(self.controller.queue) > 0:
                self.controller.next_in_queue()
        elif "instrument.configure(" in cmd:
            params = cmd[0:-1].split("instrument.configure(")[1].split(",")
            for i, param in enumerate(params):
                params[i] = param.strip(" ")  # needed when we check for setup_only
            try:
                num = int(params[0])
                self.controller.instrument_config_entry.delete(0, "end")
                self.controller.instrument_config_entry.insert(0, str(num))
                if not self.controller.script_running:
                    self.controller.queue = []

                # If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI
                # is just filled in for them how they want.
                setup_only = False
                if "setup_only=True" in params:
                    setup_only = True
                elif "setup_only =True" in params:
                    setup_only = True
                elif "setup_only = True" in params:
                    setup_only = True

                if not setup_only:
                    self.controller.queue.insert(0, {self.controller.configure_instrument: []})
                    self.controller.configure_instrument()
                elif len(self.controller.queue) > 0:
                    self.controller.next_in_queue()
            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)

        elif "sleep" in cmd:
            param = cmd[0:-1].split("sleep(")[1]
            try:
                num = float(param)
                try:
                    title = "Sleeping..."
                    label = "Sleeping..."
                    self.controller.wait_dialog.reset(title=title, label=label)
                except:
                    pass  # If there isn't already a wait dialog up, don't create one.
                elapsed = 0
                while elapsed < num - 10:
                    time.sleep(10)
                    elapsed += 10
                    self.controller.console_log.insert(END, "\t" + str(elapsed))
                remaining = num - elapsed
                time.sleep(remaining)
                self.controller.console_log.insert(END, "\tDone sleeping.\n")
                if len(self.controller.queue) > 0:
                    self.controller.next_in_queue()
            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)

        elif "move_tray(" in cmd:
            if self.controller.manual_automatic.get() == 0:
                self.controller.log("Error: Not in automatic mode")
                return False
            try:
                param = cmd.split("move_tray(")[1].strip(")")
            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False
            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -800, 800)

                except:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.move_tray: [steps, "steps"]})
                    self.controller.move_tray(steps, type="steps")
                else:
                    self.controller.log(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -800 to 800."
                    )
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False
            else:
                pos = param
                alternatives = [
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                ]  # These aren't how sample positions are specified in available_sample_positions (which has Sample 1,
                # etc) but we'll accept them.
                if pos in alternatives:
                    pos = self.controller.available_sample_positions[alternatives.index(pos)]
                elif pos.lower() == "wr":
                    pos = "WR"
                if pos in self.controller.available_sample_positions or pos == "WR":

                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.move_tray: [pos]})
                    self.controller.move_tray(pos)
                else:
                    self.controller.log("Error: " + pos + " is an invalid tray position")
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False

        elif "set_emission(" in cmd:
            if self.controller.manual_automatic.get() == 0 or self.controller.connection_tracker.pi_offline:
                print(self.controller.manual_automatic.get())
                self.controller.log("Error: Not in automatic mode")
                self.controller.queue = []
                self.controller.script_running = False
                return False
            try:
                param = cmd.split("set_emission(")[1][:-1]

            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -1000, 1000)

                except:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_emission: [steps, "steps"]})
                    self.controller.set_emission(steps, "steps")
                else:
                    self.controller.log(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -1000 to 1000."
                    )
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False
            else:
                e = param
                valid_e = utils.validate_int_input(e, self.controller.min_science_e, self.controller.max_science_e)
                if valid_e:
                    e = int(param)
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_emission: [e]})
                    self.controller.set_emission(e)
                else:
                    self.controller.log("Error: " + str(e) + " is an invalid emission angle.")
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False

        elif "set_azimuth(" in cmd:
            if self.controller.manual_automatic.get() == 0 or self.controller.connection_tracker.pi_offline:
                self.controller.log("Error: Not in automatic mode")
                self.controller.queue = []
                self.controller.script_running = False
                return False
            try:
                param = cmd.split("set_azimuth(")[1][:-1]

            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -1000, 1000)

                except:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_emission: [steps, "steps"]})
                    self.controller.set_emission(steps, "steps")
                else:
                    self.controller.log(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -1000 to 1000."
                    )
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False
            else:
                az = param
                valid_az = utils.validate_int_input(az, self.controller.min_science_az, self.controller.max_science_az)
                if valid_az:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_azimuth: [az]})
                    self.controller.set_azimuth(az)
                else:
                    self.controller.log("Error: " + str(az) + " is an invalid azimuth angle.")
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False

        # Accepts incidence angle in degrees, converts to motor position. OR accepts motor steps to move.
        elif "set_incidence(" in cmd:
            if self.controller.manual_automatic.get() == 0 or self.controller.connection_tracker.pi_offline:
                self.controller.log("Error: Not in automatic mode")
                self.controller.queue = []
                self.controller.script_running = False
                return False
            try:
                param = cmd.split("set_incidence(")[1][:-1]

            except:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -1000, 1000)

                except:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_incidence: [steps, "steps"]})
                    self.controller.set_incidence(steps, "steps")
                else:
                    self.controller.log(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -1000 to 1000."
                    )
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False
            else:
                next_science_i = param
                valid_i = utils.validate_int_input(
                    next_science_i, self.controller.min_science_i, self.controller.max_science_i
                )
                if valid_i:
                    next_science_i = int(next_science_i)

                    if not self.controller.script_running:
                        self.controller.queue = []

                    self.controller.queue.insert(0, {self.controller.set_incidence: [next_science_i]})
                    self.controller.set_incidence(next_science_i)
                else:
                    self.controller.log("Error: " + next_science_i + " is an invalid incidence angle.")
                    self.controller.queue = []
                    self.controller.script_running = False
                    return False

        elif "set_motor_azimuth" in cmd:
            if self.controller.manual_automatic.get() == 0 or self.controller.connection_tracker.pi_offline:
                self.controller.log("Error: Not in automatic mode")
                self.controller.queue = []
                self.controller.script_running = False
                return False
            az = int(cmd.split("set_motor_azimuth(")[1].strip(")"))
            valid_az = utils.validate_int_input(az, self.controller.min_motor_az, self.controller.max_motor_az)

            if valid_az:
                next_science_i, next_science_e, next_science_az = self.controller.motor_pos_to_science_pos(
                    self.controller.motor_i, self.controller.motor_e, int(az)
                )
                if not self.controller.script_running:
                    self.controller.queue = []
                self.controller.queue.insert(0, {self.controller.set_azimuth: [az]})
                self.controller.set_azimuth(az)
            else:
                self.controller.log("Error: " + str(az) + " is an invalid azimuth angle.")
                self.controller.queue = []
                self.controller.script_running = False
                return False

        elif "set_goniometer" in cmd:
            if self.controller.manual_automatic.get() == 0:
                self.controller.log("Error: Not in automatic mode")
                self.controller.queue = []
                self.controller.script_running = False
                return False
            params = cmd.split("set_goniometer(")[1].strip(")").split(",")
            if len(params) != 3:
                self.controller.log(str(len(params)))
                self.controller.log("Error: invalid display setting. Enter set_display(i, e, az")
                return

            valid_i = utils.validate_int_input(params[0], self.controller.min_science_i, self.controller.max_science_i)
            valid_e = utils.validate_int_input(params[1], self.controller.min_science_e, self.controller.max_science_e)
            valid_az = utils.validate_int_input(
                params[2], self.controller.min_science_az, self.controller.max_science_az
            )

            if not valid_i or not valid_e or not valid_az:
                self.controller.log("Error: invalid geometry")
                return

            i = int(params[0])
            e = int(params[1])
            az = int(params[2])

            current_motor = (self.controller.motor_i, self.controller.motor_e, self.controller.motor_az)
            movements = self.controller.get_movements(i, e, az, current_motor=current_motor)

            if movements is None:
                print("NO PATH FOUND")
                self.controller.log(
                    "Error: Cannot find a path from current geometry to i= "
                    + str(i)
                    + ", e="
                    + str(e)
                    + ", az="
                    + str(az)
                )

            else:
                temp_queue = []

                for movement in movements:
                    if "az" in movement:
                        next_motor_az = movement["az"]
                        if next_motor_az != self.controller.science_az:
                            temp_queue.append({self.controller.set_azimuth: [next_motor_az]})
                    elif "e" in movement:
                        next_motor_e = movement["e"]
                        print(type(next_motor_e))
                        print(type(self.controller.science_e))
                        if next_motor_e != self.controller.science_e:
                            temp_queue.append({self.controller.set_emission: [next_motor_e]})
                    elif "i" in movement:
                        next_motor_i = movement["i"]
                        if next_motor_i != self.controller.science_i:
                            temp_queue.append({self.controller.set_incidence: [next_motor_i]})
                    else:
                        print("UNEXPECTED: " + str(movement))

                self.controller.queue = temp_queue + self.controller.queue

            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()
            else:
                self.controller.script_running = False
                self.controller.queue = []
        elif cmd == "print_movements()":
            print(len(self.controller.goniometer_view.movements["i"]))
            print(len(self.controller.goniometer_view.movements["e"]))
            print(len(self.controller.goniometer_view.movements["az"]))
            print()
            print(self.controller.goniometer_view.movements)
            print()

            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()
            else:
                self.controller.script_running = False
                self.controller.queue = []

        elif "set_display" in cmd:
            params = cmd.split("set_display(")[1].strip(")").split(",")
            if len(params) != 3:
                self.controller.log(str(len(params)))
                self.controller.log("Error: invalid display setting. Enter set_display(i, e, az")
                return

            valid_i = utils.validate_int_input(params[0], self.controller.min_science_i, self.controller.max_science_i)
            valid_e = utils.validate_int_input(params[1], self.controller.min_science_e, self.controller.max_science_e)
            valid_az = utils.validate_int_input(
                params[2], self.controller.min_science_az, self.controller.max_science_az
            )

            if not valid_i or not valid_e or not valid_az:
                self.controller.log("Error: invalid geometry")
                if len(self.controller.queue) > 0:
                    self.controller.next_in_queue()
                    return

                self.controller.script_running = False
                return

            i = int(params[0])
            e = int(params[1])
            az = int(params[2])

            current_motor = (
                self.controller.goniometer_view.motor_i,
                self.controller.goniometer_view.motor_e,
                self.controller.goniometer_view.motor_az,
            )
            movements = self.controller.get_movements(i, e, az, current_motor=current_motor)

            if movements is None:
                self.controller.log(
                    "Error: Cannot find a path from current geometry to i= "
                    + str(i)
                    + ", e="
                    + str(e)
                    + ", az="
                    + str(az)
                )

            if movements is not None:
                temp_queue = []

                for movement in movements:
                    if "az" in movement:
                        next_motor_az = movement["az"]
                        temp_queue.append({self.controller.goniometer_view.set_azimuth: [next_motor_az]})
                    elif "e" in movement:
                        next_motor_e = movement["e"]
                        temp_queue.append({self.controller.goniometer_view.set_emission: [next_motor_e]})
                    elif "i" in movement:
                        next_motor_i = movement["i"]
                        temp_queue.append({self.controller.goniometer_view.set_incidence: [next_motor_i]})
                    else:
                        print("UNEXPECTED: " + str(movement))

                for item in temp_queue:
                    for func in item:
                        args = item[func]
                        func(*args)

            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()
            else:
                self.controller.script_running = False
                self.controller.queue = []

        elif "rotate_display" in cmd:
            angle = cmd.split("rotate_display(")[1].strip(")")
            valid = utils.validate_int_input(angle, -360, 360)
            if not valid:
                self.controller.log("Error: invalid geometry")
                return
            angle = int(angle)

            self.controller.goniometer_view.set_goniometer_tilt(0)

            self.controller.goniometer_view.wireframes["i"].rotate_az(angle)
            self.controller.goniometer_view.wireframes["light"].rotate_az(angle)
            self.controller.goniometer_view.wireframes["light guide"].rotate_az(angle)
            self.controller.goniometer_view.wireframes["motor az guide"].rotate_az(angle)
            self.controller.goniometer_view.wireframes["science az guide"].rotate_az(angle)

            self.controller.goniometer_view.wireframes["e"].rotate_az(angle)
            self.controller.goniometer_view.wireframes["detector"].rotate_az(angle)
            self.controller.goniometer_view.wireframes["detector guide"].rotate_az(angle)

            self.controller.goniometer_view.set_goniometer_tilt(20)

            self.controller.goniometer_view.draw_3D_goniometer(
                self.controller.goniometer_view.width, self.controller.goniometer_view.height
            )
            self.controller.goniometer_view.flip()

        elif "rotate_tray_display" in cmd:
            angle = cmd.split("rotate_tray_display(")[1].strip(")")
            valid = utils.validate_int_input(angle, -360, 360)
            if not valid:
                self.controller.log("Error: invalid geometry")
                return
            angle = int(angle)
            self.controller.goniometer_view.rotate_tray(angle)
            self.controller.goniometer_view.draw_3D_goniometer(
                self.controller.goniometer_view.width, self.controller.goniometer_view.height
            )
            self.controller.goniometer_view.flip()

        elif cmd == "end file":
            self.controller.script_running = False
            self.controller.queue = []
            if self.controller.wait_dialog is not None:
                self.controller.wait_dialog.interrupt("Success!")  # If there is a wait dialog up, make it say success.
                # There may never have been one that was made though.
                self.controller.wait_dialog.top.wm_geometry("376x140")
            return True

        else:
            self.controller.fail_script_command("Error: could not parse command " + cmd)
            return False

        self.controller.text_only = False
        return True
