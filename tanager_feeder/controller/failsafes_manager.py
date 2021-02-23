import sys
import time
from tkinter import Entry, Button, Label, Checkbutton, Toplevel, Frame, BOTH, LEFT, X, IntVar
from typing import List, Optional

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder import utils


class FailsafesManager:
    def __init__(self, controller: utils.ControllerType):
        self.controller = controller
        self.tk_format = utils.TkFormat(self.controller.config_info)

        # check before taking spectra whether conditions have been met regarding when the last white reference was, etc
        self.wrfailsafe = IntVar()
        self.wrfailsafe.set(1)
        self.optfailsafe = IntVar()
        self.optfailsafe.set(1)
        self.angles_failsafe = IntVar()
        self.angles_failsafe.set(1)
        self.labelfailsafe = IntVar()
        self.labelfailsafe.set(1)
        self.wr_angles_failsafe = IntVar()
        self.wr_angles_failsafe.set(1)
        self.anglechangefailsafe = IntVar()
        self.anglechangefailsafe.set(1)

        self.wr_time = None
        self.opt_time = None
        self.angles_change_time = None
        self.settings_top = None

        self.wrfailsafe_check = None
        self.wr_timeout_entry = None
        self.optfailsafe_check = None
        self.opt_timeout_entry = None
        self.angles_failsafe_check = None
        self.label_failsafe_check = None
        self.wr_angles_failsafe_check = None
        self.anglechangefailsafe_check = None

    def show(self) -> None:
        self.settings_top = Toplevel(self.controller.master)
        self.settings_top.wm_title("Failsafe Settings")
        settings_frame = Frame(self.settings_top, bg=self.tk_format.bg, pady=2 * self.tk_format.pady, padx=15)
        settings_frame.pack()

        failsafe_title_frame = Frame(settings_frame, bg=self.tk_format.bg)
        failsafe_title_frame.pack(pady=(10, 0), fill=X, expand=True)
        failsafe_label0 = Label(
            failsafe_title_frame,
            fg=self.tk_format.textcolor,
            text="Failsafes:                                                                      ",
            bg=self.tk_format.bg,
        )
        failsafe_label0.pack(side=LEFT)

        failsafe_frame = Frame(settings_frame, bg=self.tk_format.bg, pady=self.tk_format.pady)
        failsafe_frame.pack(fill=BOTH, expand=True, padx=(10, 10))

        wr_failsafe_check_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        wr_failsafe_check_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        self.wrfailsafe_check = Checkbutton(
            wr_failsafe_check_frame,
            fg=self.tk_format.textcolor,
            text="Prompt if no white reference has been taken.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.wrfailsafe,
            selectcolor=self.tk_format.check_bg,
        )
        self.wrfailsafe_check.pack(side=LEFT)
        if self.wrfailsafe.get():
            self.wrfailsafe_check.select()

        wr_timeout_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        wr_timeout_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        wr_timeout_label = Label(
            wr_timeout_frame, fg=self.tk_format.textcolor, text="Timeout (minutes):", bg=self.tk_format.bg
        )
        wr_timeout_label.pack(side=LEFT, padx=(20, 0))
        self.wr_timeout_entry = Entry(
            wr_timeout_frame,
            bd=self.tk_format.bd,
            width=10,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.wr_timeout_entry.pack(side=LEFT, padx=(0, 20))
        self.wr_timeout_entry.insert(0, "8")

        optfailsafe_check_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        optfailsafe_check_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        self.optfailsafe_check = Checkbutton(
            optfailsafe_check_frame,
            fg=self.tk_format.textcolor,
            text="Prompt if the instrument has not been optimized.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            selectcolor=self.tk_format.check_bg,
            variable=self.optfailsafe,
        )
        self.optfailsafe_check.pack(side=LEFT)
        if self.optfailsafe.get():
            self.optfailsafe_check.select()

        opt_timeout_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        opt_timeout_frame.pack(pady=self.tk_format.pady, fill=X, expand=True, padx=(20, 5))
        opt_timeout_label = Label(
            opt_timeout_frame, fg=self.tk_format.textcolor, text="Timeout (minutes):", bg=self.tk_format.bg
        )
        opt_timeout_label.pack(side=LEFT, padx=(20, 0))
        self.opt_timeout_entry = Entry(
            opt_timeout_frame,
            bd=self.tk_format.bd,
            width=10,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.opt_timeout_entry.pack(side=LEFT, padx=(0, 20))
        self.opt_timeout_entry.insert(0, "60")
        filler_label = Label(
            opt_timeout_frame, bg=self.tk_format.bg, fg=self.tk_format.textcolor, text="              "
        )
        filler_label.pack(side=LEFT)

        angles_failsafe_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        angles_failsafe_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        self.angles_failsafe_check = Checkbutton(
            angles_failsafe_frame,
            fg=self.tk_format.textcolor,
            text="Check validity of emission and incidence angles.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            selectcolor=self.tk_format.check_bg,
            variable=self.angles_failsafe,
        )
        if self.angles_failsafe.get():
            self.angles_failsafe_check.select()

        label_failsafe_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        label_failsafe_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        self.label_failsafe_check = Checkbutton(
            label_failsafe_frame,
            fg=self.tk_format.textcolor,
            text="Require a label for each spectrum.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            selectcolor=self.tk_format.check_bg,
            variable=self.labelfailsafe,
        )
        self.label_failsafe_check.pack(pady=(6, 5), side=LEFT, padx=(0, 20))
        if self.labelfailsafe.get():
            self.label_failsafe_check.select()

        wr_angles_failsafe_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        wr_angles_failsafe_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        self.wr_angles_failsafe_check = Checkbutton(
            wr_angles_failsafe_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text="Require a new white reference at each viewing geometry             ",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.wr_angles_failsafe,
        )
        self.wr_angles_failsafe_check.pack(pady=(6, 5), side=LEFT)
        if self.wr_angles_failsafe.get():
            self.wr_angles_failsafe_check.select()

        wrap_frame = Frame(failsafe_frame, bg=self.tk_format.bg)
        wrap_frame.pack(pady=self.tk_format.pady, padx=(20, 5), fill=X, expand=True)
        self.anglechangefailsafe_check = Checkbutton(
            wrap_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text="Remind me to check the goniometer if the viewing geometry changes.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.anglechangefailsafe,
        )

        failsafes_ok_button = Button(failsafe_frame, text="Ok", command=self.settings_top.destroy)
        failsafes_ok_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            width=15,
        )
        failsafes_ok_button.pack(pady=self.tk_format.pady)
        self.settings_top.resizable(False, False)

    # If the user has failsafes activated, check that requirements are met. Always require a valid number of spectra.
    # Different requirements are checked depending on what the function func is that will be called next (opt, wr, take
    # spectrum, acquire)
    def check_optional_input(self, func, args: Optional[List] = None, warnings: str = "") -> bool:
        if args is None:
            args = []
        label = warnings
        now = int(time.time())
        incidence = self.controller.incidence_entries[0].get()
        emission = self.controller.emission_entries[0].get()
        azimuth = self.controller.azimuth_entries[0].get()

        if self.controller.manual_automatic.get() == 0:
            # pylint: disable = comparison-with-callable
            warnings = self.controller.check_viewing_geom_for_manual_operation()
            label += warnings

            if self.optfailsafe.get() and func != self.controller.opt:
                try:
                    opt_limit = int(float(self.opt_timeout_entry.get())) * 60
                except (ValueError, AttributeError):
                    opt_limit = sys.maxsize
                if self.opt_time is None:
                    label += "The instrument has not been optimized.\n\n"
                elif now - self.opt_time > opt_limit:
                    minutes = str(int((now - self.opt_time) / 60))
                    seconds = str((now - self.opt_time) % 60)
                    if int(minutes) > 0:
                        label += (
                            "The instrument has not been optimized for "
                            + minutes
                            + " minutes "
                            + seconds
                            + " seconds.\n\n"
                        )
                    else:
                        label += "The instrument has not been optimized for " + seconds + " seconds.\n\n"
                if self.opt_time is not None:
                    if self.angles_change_time is None:
                        pass
                    elif self.opt_time < self.angles_change_time:
                        valid_i = utils.validate_int_input(
                            incidence, self.controller.min_science_i, self.controller.max_science_i
                        )
                        valid_e = utils.validate_int_input(
                            emission, self.controller.min_science_e, self.controller.max_science_e
                        )
                        valid_az = utils.validate_int_input(
                            azimuth, self.controller.min_science_az, self.controller.max_science_az
                        )
                        if valid_i and valid_e and valid_az:
                            label += "The instrument has not been optimized at this geometry.\n\n"

            if self.wrfailsafe.get() and func != self.controller.wr and func != self.controller.opt:

                try:
                    wr_limit = int(float(self.wr_timeout_entry.get())) * 60
                except (ValueError, AttributeError):
                    wr_limit = sys.maxsize
                if self.wr_time is None:
                    label += "No white reference has been taken.\n\n"
                elif self.opt_time is not None and self.opt_time > self.wr_time:
                    label += "No white reference has been taken since the instrument was optimized.\n\n"
                elif int(self.controller.instrument_config_entry.get()) != int(self.controller.spec_config_count):
                    label += "No white reference has been taken while averaging this number of spectra.\n\n"
                elif self.controller.spec_config_count is None:
                    label += "No white reference has been taken while averaging this number of spectra.\n\n"
                elif now - self.wr_time > wr_limit:
                    minutes = str(int((now - self.wr_time) / 60))
                    seconds = str((now - self.wr_time) % 60)
                    if int(minutes) > 0:
                        label += (
                            " No white reference has been taken for "
                            + minutes
                            + " minutes "
                            + seconds
                            + " seconds.\n\n"
                        )
                    else:
                        label += " No white reference has been taken for " + seconds + " seconds.\n\n"
            if self.wr_angles_failsafe.get() and func != self.controller.wr:

                if self.angles_change_time is not None and self.wr_time is not None and func != self.controller.opt:
                    if self.angles_change_time > self.wr_time + 1:
                        valid_i = utils.validate_int_input(
                            incidence, self.controller.min_science_i, self.controller.max_science_i
                        )
                        valid_e = utils.validate_int_input(
                            emission, self.controller.min_science_e, self.controller.max_science_e
                        )
                        valid_az = utils.validate_int_input(
                            azimuth, self.controller.min_science_az, self.controller.max_science_az
                        )
                        if valid_i and valid_e and valid_az:
                            label += " No white reference has been taken at this viewing geometry.\n\n"

        if self.labelfailsafe.get() and func != self.controller.opt and func != self.controller.wr:
            if self.controller.sample_label_entries[self.controller.current_sample_gui_index].get() == "":
                label += "This sample has no label.\n\n"
        for entry in self.controller.sample_label_entries:
            sample_label = entry.get()
            newlabel = self.controller.validate_sample_name(sample_label)
            if newlabel != sample_label:
                entry.delete(0, "end")
                if newlabel == "":
                    newlabel = "sample"

                entry.insert(0, newlabel)
                label += (
                    "'"
                    + sample_label
                    + "' is an invalid sample label.\nSample will be labeled as '"
                    + newlabel
                    + "' instead.\n\n"
                )
                self.controller.log(
                    "Warning: '"
                    + sample_label
                    + "' is an invalid sample label. Removing reserved characters and expressions."
                )

        if label != "":  # if we came up with errors
            title = "Warning!"

            buttons = {
                "yes": {
                    # if the user says they want to continue anyway, run take spectrum again but this time with
                    # override=True
                    func: args
                },
                "no": {},
            }
            label = "Warning!\n\n" + label
            label += "\nDo you want to continue?"
            Dialog(self.controller, title, label, buttons)
            return False
        # if there were no errors
        return True
