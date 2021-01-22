from tkinter import Frame, Label, Entry, LEFT, OptionMenu, StringVar

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder import utils
from tanager_feeder.dialogs.error_dialog import ErrorDialog


class ConfigDialog(Dialog):
    def __init__(self, controller, title, label, values={}, buttons={"ok": {}, "cancel": {}}):
        super().__init__(controller, title, label, buttons, allow_exit=False)
        self.values = values
        self.entry_frame = Frame(self.top, bg=self.bg)
        self.entry_frame.pack(pady=(10, 20))
        self.labels = {}
        self.entries = {}
        self.mins = {}
        self.maxes = {}
        for val in values:
            frame = Frame(self.entry_frame, bg=self.bg)
            frame.pack(pady=(5, 5))
            self.labels[val] = Label(frame, text="{0:>15}".format(val) + ": ", fg=self.textcolor, bg=self.bg)
            self.labels[val].pack(side=LEFT, padx=(3, 3))
            if val != "Tray position":
                self.entries[val] = Entry(
                    frame,
                    bg=self.entry_background,
                    selectbackground=self.selectbackground,
                    selectforeground=self.selectforeground,
                )
                self.entries[val].pack(side=LEFT)
            else:
                self.entries[val] = StringVar()
                self.entries[val].set("White reference")
                print(self.entries["Tray position"].get())
                menu = OptionMenu(
                    frame,
                    self.entries[val],
                    "{0:15}".format("White reference"),
                    "{0:18}".format("1"),
                    "2          ",
                    "3          ",
                    "4          ",
                    "5          ",
                )
                menu.configure(width=15, highlightbackground=self.controller.highlightbackgroundcolor)
                menu.pack()

        self.set_buttons(buttons)

    def ok(self):
        bad_vals = []
        for val in self.values:
            self.mins[val] = self.values[val][1]
            self.maxes[val] = self.values[val][2]
            valid = utils.validate_float_input(
                self.entries[val].get(), self.mins[val], self.maxes[val]
            )  # Weird for tray position - not valid for white reference
            if val == "Tray position":
                valid = True
            if not valid:
                bad_vals.append(val)

        valid_sep = True  # Used to have to be > 10 degrees, fine if not.

        if len(bad_vals) == 0 and valid_sep:
            pos = self.entries["Tray position"].get()
            if pos == "White reference":
                pos = -1

            incidence = float(self.entries["Incidence"].get())
            emission = float(self.entries["Emission"].get())
            azimuth = utils.AZIMUTH_HOME
            self.controller.queue[0][self.controller.configure_pi] = [incidence, emission, pos]

            self.top.destroy()
            dict = self.buttons["ok"]
            for func in dict:
                args = dict[func]
                func(*args)
        else:
            err_str = "Error: Invalid "
            if len(bad_vals) == 1:
                for val in bad_vals:
                    err_str += (
                        val.lower()
                        + " value.\nPlease enter a number from "
                        + str(self.mins[val])
                        + " to "
                        + str(self.maxes[val])
                        + "."
                    )
            elif valid_sep:
                err_str += "input. Please enter the following:\n\n"
                for val in bad_vals:
                    err_str += val + " from " + str(self.mins[val]) + " to " + str(self.maxes[val]) + "\n"
            else:
                err_str += (
                    "angular separation.\nThe detector and its arm must be at least "
                    + str(self.controller.required_angular_separation)
                    + " degrees away from the light source."
                )
            dialog = ErrorDialog(self.controller, title="Error: Invalid Input", label=err_str)
