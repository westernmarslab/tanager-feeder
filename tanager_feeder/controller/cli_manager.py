import time
from tkinter import END

from tanager_feeder import utils


class CliManager:
    def __init__(self, controller: utils.ControllerType):
        self.controller = controller

    def execute_cmd(
        self, cmd
    ):  # In a separate method because that allows it to be spun off in a new thread, so tkinter mainloop continues,
        # which means that the console log gets updated immediately e.g. if you say sleep(10) it will say sleep up in
        # the log while it is sleeping.

        if cmd == "wr()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.wr: [True, False]})
            self.controller.queue.insert(1, {self.controller.take_spectrum: [True, True, False]})
            self.controller.wr(True, False)
            return True

        if cmd == "opt()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.opt: [True, False]})
            self.controller.opt(True, False)  # override=True, setup complete=False
            return True

        if cmd == "goniometer.configure(MANUAL)":
            self.controller.set_manual_automatic(force=0)
            return True

        elif cmd == "goniometer.configure(AUTOMATIC)":
            self.controller.set_manual_automatic(force=1)
            return True

        if cmd == "collect_garbage()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.take_spectrum: [True, False, True]})
            self.controller.take_spectrum(True, False, True)
            return True

        if cmd == "acquire()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.acquire()
            return True

        if cmd == "take_spectrum()":
            if not self.controller.script_running:
                self.controller.queue = []
            self.controller.queue.insert(0, {self.controller.take_spectrum: [True, True, False]})
            self.controller.take_spectrum(True, True, False)
            return True

        if "setup_geom(" in cmd:  # params are i, e, index=0
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
                        index = int(self.get_val(params[2]))
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
                        self.controller.azimuth_entries[index].delete(0, "end")
                        self.controller.azimuth_entries[index].insert(0, params[2])
            return True

        if "add_geom(" in cmd:  # params are i, e. Will not overwrite existing geom.
            print(cmd)
            params = cmd[0:-1].split("add_geom(")[1].split(",")
            print(params)
            if len(params) != 3:
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
            return True
        if "setup_geom_range(" in cmd:
            if self.controller.manual_automatic.get() == 0:
                self.controller.fail_script_command("Error: Not in automatic mode")
                return False
            self.controller.set_individual_range(force=1)
            params = cmd[0:-1].split("setup_geom_range(")[1].split(",")
            for param in params:
                if "i_start" in param:
                    self.controller.light_start_entry.delete(0, "end")
                    try:
                        self.controller.light_start_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse initial incidence angle")
                        return False
                elif "i_end" in param:
                    self.controller.light_end_entry.delete(0, "end")
                    try:
                        self.controller.light_end_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse final incidence angle")
                        return False
                elif "e_start" in param:
                    self.controller.detector_start_entry.delete(0, "end")
                    try:
                        self.controller.detector_start_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse initial emission angle")
                        return False
                elif "e_end" in param:
                    self.controller.detector_end_entry.delete(0, "end")
                    try:
                        self.controller.detector_end_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse final emission angle")
                        return False
                elif "az_start" in param:
                    self.controller.azimuth_start_entry.delete(0, "end")
                    try:
                        self.controller.azimuth_start_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.log("Error: Unable to parse initial azimuth angle")
                        self.controller.queue = []
                        self.controller.script_running = False
                elif "az_end" in param:
                    self.controller.azimuth_end_entry.delete(0, "end")
                    try:
                        self.controller.azimuth_end_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse final azimuth angle")
                        return False
                elif "i_increment" in param:
                    self.controller.light_increment_entry.delete(0, "end")
                    try:
                        self.controller.light_increment_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse incidence angle increment.")
                        return False
                elif "e_increment" in param:
                    self.controller.detector_increment_entry.delete(0, "end")
                    try:
                        self.controller.detector_increment_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse emission angle increment.")
                        return False
                elif "az_increment" in param:
                    self.controller.azimuth_increment_entry.delete(0, "end")
                    try:
                        self.controller.azimuth_increment_entry.insert(0, self.get_val(param))
                    except IndexError:
                        self.controller.fail_script_command("Error: Unable to parse azimuth angle increment.")
                        return False
            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()
            return True

        if "set_samples(" in cmd:
            try:
                params = cmd[0:-1].split("set_samples(")[1].split(",")
            except IndexError:
                self.controller.fail_script_command(
                    "Error: could not parse command "
                    + cmd
                    + ". Use the format set_samples({position}={name}) e.g. set_samples(1=Basalt)"
                )
                return False
            if params == [""]:
                params = []

            # First clear all existing sample names
            while len(self.controller.sample_frames) > 1:
                self.controller.remove_sample(-1)
            utils.set_text(self.controller.sample_label_entries[0], "")

            # Then add in samples in order specified in params. Each param should be a sample name and pos.
            skip_count = 0  # If a param is badly formatted, we'll skip it. Keep track of how many are skipped in order
            # to index labels, etc right.
            for i, param in enumerate(params):
                # TODO: test this code
                try:
                    pos = param.split("=")[0].strip(" ")
                    name = self.get_val(param)
                except IndexError:
                    self.controller.fail_script_command(
                        "Error: could not parse command "
                        + cmd
                        + ". Use the format set_samples({position}={name}) e.g. set_samples(1=Basalt)"
                    )
                    skip_count += 1
                    continue
                valid_pos = utils.validate_int_input(pos, 1, 5)
                if (
                    self.controller.available_sample_positions[int(pos) - 1] in self.controller.taken_sample_positions
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

                if valid_pos:
                    utils.set_text(self.controller.sample_label_entries[i - skip_count], name)
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
            return True

        if "set_spec_save(" in cmd:
            self.controller.unfreeze()
            try:
                params = cmd[0:-1].split("set_spec_save(")[1].split(",")
            except IndexError:
                self.controller.fail_script_command("Error: Could not parse command.")
                return False

            for i, param in enumerate(params):
                params[i] = param.strip(" ")  # Need to do this before looking for setup only
                if "directory" in param:
                    try:
                        save_dir = self.get_val(param)
                    except IndexError:
                        self.controller.fail_script_command("Error: Could not parse command.")
                        return False
                    self.controller.spec_save_dir_entry.delete(0, "end")
                    self.controller.spec_save_dir_entry.insert(0, save_dir)
                elif "basename" in param:
                    try:
                        basename = self.get_val(param)
                    except IndexError:
                        self.controller.fail_script_command("Error: Could not parse command.")
                        return False
                    self.controller.spec_basename_entry.delete(0, "end")
                    self.controller.spec_basename_entry.insert(0, basename)
                elif "num" in param:
                    try:
                        num = self.get_val(param)
                    except IndexError:
                        self.controller.fail_script_command("Error: Could not parse command.")
                        return False
                    self.controller.spec_startnum_entry.delete(0, "end")
                    self.controller.spec_startnum_entry.insert(0, num)

            if not self.controller.script_running:
                self.controller.queue = []

            # If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI is
            # just filled in for them how they want.
            setup_only = False
            for param in params:
                if param.replace(" ", "") == "setup_only":
                    setup_only = True

            if not setup_only:
                self.controller.queue.insert(0, {self.controller.set_save_config: []})
                self.controller.set_save_config()
            elif len(self.controller.queue) > 0:
                self.controller.next_in_queue()
            return True

        if "instrument.configure(" in cmd:
            params = cmd[0:-1].split("instrument.configure(")[1].split(",")
            for i, param in enumerate(params):
                params[i] = param.strip(" ")  # needed when we check for setup_only
            try:
                num = int(params[0])
            except ValueError:
                self.controller.fail_script_command(f"Error: {params[0]} is not a valid number.")
                return False

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
            return True

        if "sleep" in cmd:
            try:
                param = cmd[0:-1].split("sleep(")[1]
            except IndexError:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False
            try:
                num = float(param)
            except ValueError:
                self.controller.fail_script_command(f"Error: {param} is not a valid number.")
                return False
            try:
                title = "Sleeping..."
                label = "Sleeping..."
                self.controller.wait_dialog.reset(title=title, label=label)
            except AttributeError:
                # TODO: confirm attributeError is correct type
                pass  # If there isn't already a wait dialog up, don't create one.
            elapsed = 0
            while elapsed < num - 10:
                time.sleep(10)
                elapsed += 10
                self.controller.log.insert("\t" + str(elapsed))
            remaining = num - elapsed
            time.sleep(remaining)
            self.controller.log.insert("\tDone sleeping.\n")
            if len(self.controller.queue) > 0:
                self.controller.next_in_queue()
            return True

        if "move_tray(" in cmd:
            if self.controller.connection_manager.pi_offline:
                self.controller.fail_script_command("Error: Pi offline.")
                return False
            try:
                param = cmd.split("move_tray(")[1].strip(")")
            except IndexError:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False
            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -800, 800)
                except IndexError:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                except ValueError:
                    val = param.split("=")[-1]
                    self.controller.fail_script_command(f"Error: {val} is not a valid number.")
                    return False

                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.move_tray: [steps, "steps"]})
                    self.controller.move_tray(steps, unit="steps")
                else:
                    self.controller.fail_script_command(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -800 to 800."
                    )
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
                    self.controller.fail_script_command("Error: " + pos + " is an invalid tray position")
                    return False
            return True

        if "set_emission(" in cmd:
            if self.controller.connection_manager.pi_offline:
                self.controller.fail_script_command("Error: Pi offline.")
                return False
            try:
                param = cmd.split("set_emission(")[1][:-1]
            except IndexError:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -1000, 1000)
                except IndexError:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                except ValueError:
                    val = param.split("=")[-1]
                    self.controller.fail_script_command(f"Error: {val} is not a valid number.")
                    return False

                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_emission: [steps, "steps"]})
                    self.controller.set_emission(steps, "steps")
                else:
                    self.controller.fail_script_command(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -1000 to 1000."
                    )
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
                    self.controller.fail_script_command("Error: " + str(e) + " is an invalid emission angle.")
                    return False
            return True

        if "set_azimuth(" in cmd:
            if self.controller.connection_manager.pi_offline:
                self.controller.fail_script_command("Error: Pi offline.")
                return False
            try:
                param = cmd.split("set_azimuth(")[1][:-1]
            except IndexError:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -1000, 1000)
                except IndexError:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                except ValueError:
                    val = param.split("=")[-1]
                    self.controller.fail_script_command(f"Error: {val} is not a valid number.")
                    return False
                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_emission: [steps, "steps"]})
                    self.controller.set_emission(steps, "steps")
                else:
                    self.controller.fail_script_command(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -1000 to 1000."
                    )
                    return False
            else:
                az = param
                valid_az = utils.validate_int_input(az, self.controller.min_science_az, self.controller.max_science_az)
                if valid_az:
                    az = int(az)
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_azimuth: [az]})
                    self.controller.set_azimuth(az)
                else:
                    self.controller.fail_script_command("Error: " + str(az) + " is an invalid azimuth angle.")
                    return False
            return True

        # Accepts incidence angle in degrees, converts to motor position. OR accepts motor steps to move.
        if "set_incidence(" in cmd:
            if self.controller.connection_manager.pi_offline:
                self.controller.fail_script_command("Error: Pi offline.")
                return False
            try:
                param = cmd.split("set_incidence(")[1][:-1]
            except IndexError:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if "steps" in param:
                try:
                    steps = int(param.split("=")[-1])
                    valid_steps = utils.validate_int_input(steps, -1000, 1000)
                except IndexError:
                    self.controller.fail_script_command("Error: could not parse command " + cmd)
                    return False
                except ValueError:
                    val = param.split("=")[-1]
                    self.controller.fail_script_command(f"Error: {val} is not a valid number.")
                    return False
                if valid_steps:
                    if not self.controller.script_running:
                        self.controller.queue = []
                    self.controller.queue.insert(0, {self.controller.set_incidence: [steps, "steps"]})
                    self.controller.set_incidence(steps, "steps")
                else:
                    self.controller.fail_script_command(
                        "Error: " + str(steps) + " is not a valid number of steps. Enter an integer from -1000 to 1000."
                    )
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
                    self.controller.fail_script_command("Error: " + next_science_i + " is an invalid incidence angle.")
                    return False
            return True

        if "set_motor_azimuth" in cmd:
            if self.controller.manual_automatic.get() == 0 or self.controller.connection_manager.pi_offline:
                self.controller.fail_script_command("Error: Not in automatic mode")
                return False
            try:
                az = cmd.split("set_motor_azimuth(")[1].strip(")")
            except IndexError:
                self.controller.fail_script_command(f"Error: could not parse command: {cmd}")
                return False

            valid_az = utils.validate_int_input(az, self.controller.min_motor_az, self.controller.max_motor_az)
            if valid_az:
                az = int(az)
                if not self.controller.script_running:
                    self.controller.queue = []
                self.controller.queue.insert(0, {self.controller.set_azimuth: [az]})
                self.controller.set_azimuth(az)
            else:
                self.controller.fail_script_command("Error: " + str(az) + " is an invalid azimuth angle.")
                return False
            return True

        if "set_goniometer" in cmd:
            try:
                params = cmd.split("set_goniometer(")[1].strip(")").split(",")
            except IndexError:
                self.controller.fail_script_command("Error: could not parse command " + cmd)
                return False

            if len(params) != 3:
                self.controller.fail_script_command("Error: invalid display setting. Enter set_display(i, e, az")
                return False

            valid_i = utils.validate_int_input(params[0], self.controller.min_science_i, self.controller.max_science_i)
            valid_e = utils.validate_int_input(params[1], self.controller.min_science_e, self.controller.max_science_e)
            valid_az = utils.validate_int_input(
                params[2], self.controller.min_science_az, self.controller.max_science_az
            )

            if not valid_i or not valid_e or not valid_az:
                self.controller.fail_script_command("Error: invalid geometry")
                return False

            i = int(params[0])
            e = int(params[1])
            az = int(params[2])

            movements = self.controller.get_movements(i, e, az)

            if movements is None:
                self.controller.fail_script_command(
                    "Error: Cannot find a path from current geometry to i= "
                    + str(i)
                    + ", e="
                    + str(e)
                    + ", az="
                    + str(az)
                )
                return False

            temp_queue = []

            for movement in movements:
                if "az" in movement:
                    next_motor_az = movement["az"]
                    if next_motor_az != self.controller.science_az:
                        temp_queue.append({self.controller.set_azimuth: [next_motor_az]})
                elif "e" in movement:
                    next_motor_e = movement["e"]
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
            return True

        if cmd == "print_movements()":
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
            return True

        if "set_display" in cmd:
            try:
                params = cmd.split("set_display(")[1].strip(")").split(",")
            except IndexError:
                self.controller.fail_script_command(f"Error: could not parse command: {cmd}")
                return False
            if len(params) != 3:
                self.controller.fail_script_command("Error: invalid display setting. Enter set_display(i, e, az")
                return False

            valid_i = utils.validate_int_input(params[0], self.controller.min_science_i, self.controller.max_science_i)
            valid_e = utils.validate_int_input(params[1], self.controller.min_science_e, self.controller.max_science_e)
            valid_az = utils.validate_int_input(
                params[2], self.controller.min_science_az, self.controller.max_science_az
            )

            if not valid_i or not valid_e or not valid_az:
                self.controller.fail_script_command("Error: invalid geometry")
                return False

            i = int(params[0])
            e = int(params[1])
            az = int(params[2])

            movements = self.controller.get_movements(i, e, az)

            if movements is None:
                self.controller.fail_script_command(
                    "Error: Cannot find a path from current geometry to i= "
                    + str(i)
                    + ", e="
                    + str(e)
                    + ", az="
                    + str(az)
                )
                return False

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
            return True

        if "rotate_display" in cmd:
            try:
                angle = cmd.split("rotate_display(")[1].strip(")")
            except IndexError:
                self.controller.fail_script_command(f"Error: could not parse command: {cmd}")
                return False

            valid = utils.validate_int_input(angle, -360, 360)
            if not valid:
                self.controller.fail_script_command("Error: invalid geometry")
                return False

            angle = int(angle)
            self.controller.goniometer_view.rotate_display(angle)

            self.controller.goniometer_view.draw_3D_goniometer(
                self.controller.goniometer_view.width, self.controller.goniometer_view.height
            )
            self.controller.goniometer_view.flip()
            return True

        if "rotate_tray_display" in cmd:
            try:
                angle = cmd.split("rotate_tray_display(")[1].strip(")")
            except IndexError:
                self.controller.fail_script_command(f"Error: could not parse command: {cmd}")
                return False

            valid = utils.validate_int_input(angle, -360, 360)
            if not valid:
                self.controller.fail_script_command("Error: invalid geometry")
                return False

            angle = int(angle)
            self.controller.goniometer_view.rotate_tray(angle)
            self.controller.goniometer_view.draw_3D_goniometer(
                self.controller.goniometer_view.width, self.controller.goniometer_view.height
            )
            self.controller.goniometer_view.flip()
            return True

        if cmd == "end file":
            self.controller.script_running = False
            self.controller.queue = []
            self.controller.unfreeze()
            self.controller.console.console_entry.delete(0, END)
            self.controller.console.user_cmds.pop(0)
            if self.controller.wait_dialog is not None:
                self.controller.wait_dialog.interrupt("Success!")  # If there is a wait dialog up, make it say success.
                # There may never have been one that was made though.
                self.controller.wait_dialog.top.wm_geometry("376x140")
            return True

        self.controller.fail_script_command("Error: could not parse command " + cmd)
        return False

    @staticmethod
    def get_val(param):
        return param.split("=")[1].strip(" ").strip('"').strip("'")
