from tkinter import Entry, Label, Checkbutton, Frame, LEFT, EXTENDED, END, IntVar
from typing import List, Dict, Tuple

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.plotter.tab import Tab
from tanager_feeder import utils


class EditPlotManager:
    def __init__(self, controller: utils.ControllerType):
        self.controller = controller
        self.tab = None
        self.tk_format = utils.TkFormat(self.controller.config_info)

        self.exclude_specular = IntVar()
        self.edit_plot_dialog = None
        self.plot_samples_listbox = None
        self.i_entry = None
        self.e_entry = None
        self.az_entry = None
        self.new_plot_title_entry = None
        self.exclude_specular_check = None
        self.spec_tolerance_entry = None

    def show(self, tab: Tab, existing_sample_indices: List, sample_options: List, existing_geoms: Dict, current_title: str):
        self.tab = tab
        buttons = {
            "ok": {
                self.select_tab: [],
                # The lambda sends a list of the currently selected samples back to the tab along with the new title
                # and selected incidence/emission angles
                lambda: tab.set_samples(
                    list(map(lambda y: sample_options[y], self.plot_samples_listbox.curselection())),
                    self.new_plot_title_entry.get(),
                    *self.check_angle_lists(self.i_entry.get(), self.e_entry.get(), self.az_entry.get()),
                    self.exclude_specular.get(),
                    self.spec_tolerance_entry.get(),
                ): [],
            }
        }

        self.edit_plot_dialog = Dialog(self.controller, "Edit Plot", "\nPlot title:", buttons=buttons)
        self.new_plot_title_entry = Entry(
            self.edit_plot_dialog.top,
            width=20,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.new_plot_title_entry.insert(0, current_title)
        self.new_plot_title_entry.pack()

        sample_label = Label(
            self.edit_plot_dialog.top,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="\nSamples:",
        )
        sample_label.pack(pady=(0, 10))
        self.plot_samples_listbox = utils.ScrollableListbox(
            self.edit_plot_dialog.top,
            self.tk_format.bg,
            self.tk_format.entry_background,
            self.tk_format.listboxhighlightcolor,
            selectmode=EXTENDED,
        )

        geom_label = Label(
            self.edit_plot_dialog.top,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="\nEnter incidence and emission angles to plot,\nor leave blank to plot all:\n",
        )
        geom_label.pack()
        geom_frame = Frame(self.edit_plot_dialog.top)
        geom_frame.pack(padx=(20, 20), pady=(0, 10))
        i_label = Label(
            geom_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="i: ",
        )
        i_label.pack(side=LEFT)
        self.i_entry = Entry(
            geom_frame,
            width=8,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        for i, incidence in enumerate(existing_geoms["i"]):
            if i == 0:
                self.i_entry.insert(0, str(incidence))
            else:
                self.i_entry.insert("end", "," + str(incidence))

        self.i_entry.pack(side=LEFT)

        e_label = Label(
            geom_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="    e: ",
        )
        e_label.pack(side=LEFT)
        self.e_entry = Entry(
            geom_frame,
            width=8,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        for i, emission in enumerate(existing_geoms["e"]):
            if i == 0:
                self.e_entry.insert(0, str(emission))
            else:
                self.e_entry.insert("end", "," + str(emission))
        self.e_entry.pack(side=LEFT)

        az_label = Label(
            geom_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="    az: ",
        )
        az_label.pack(side=LEFT)
        self.az_entry = Entry(
            geom_frame,
            width=8,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        for i, azimuth in enumerate(existing_geoms["az"]):
            if i == 0:
                self.az_entry.insert(0, str(azimuth))
            else:
                self.az_entry.insert("end", "," + str(azimuth))
        self.az_entry.pack(side=LEFT)

        exclude_specular_frame = Frame(
            self.edit_plot_dialog.top, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        exclude_specular_frame.pack()

        self.exclude_specular_check = Checkbutton(
            exclude_specular_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text="  Exclude specular angles (+/-",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.exclude_specular,
        )
        self.exclude_specular_check.pack(side=LEFT)

        self.spec_tolerance_entry = Entry(
            exclude_specular_frame,
            width=4,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )

        self.spec_tolerance_entry.pack(side=LEFT)
        spec_tolerance_label = Label(
            exclude_specular_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="\u00B0)",
        )
        spec_tolerance_label.pack(side=LEFT)

        if tab.exclude_specular:
            self.exclude_specular_check.select()
            self.spec_tolerance_entry.insert(0, tab.specularity_tolerance)

        for option in sample_options:
            self.plot_samples_listbox.insert(END, option)

        for i in existing_sample_indices:
            self.plot_samples_listbox.select_set(i)
        self.plot_samples_listbox.config(height=8)

    def check_angle_lists(self, incidences: str, emissions: str, azimuths: str) -> Tuple[List, List, List]:
        def check_list(list_to_check: str) -> Tuple[List, List]:
            invalid_list = []
            list_to_check = list_to_check.split(",")
            if "None" in list_to_check or "none" in list_to_check:
                while "None" in list_to_check:
                    list_to_check.remove("None")
                while "none" in list_to_check:
                    list_to_check.remove("none")
                list_to_check.append(None)
            if list_to_check == [""]:
                list_to_check = []
            print(list_to_check)
            # If e.g. %5 is included in the list, include all angles where angle % 5 == 0
            n = 0
            while n < len(list_to_check):
                angle = list_to_check[n]
                if "%" in str(angle):
                    try:
                        val = int(str(angle).replace("%", ""))
                    except ValueError:
                        invalid_list.append(angle)
                        continue
                    for k in range(-70, 171):
                        if k % val == 0:
                            list_to_check.insert(n, k)
                            n+=1
                    list_to_check.remove(angle)
                    n-=1
                n+=1

            for n, angle in enumerate(list_to_check):
                if angle is not None:
                    try:
                        list_to_check[n] = int(angle)
                    except ValueError:
                        invalid_list.append(angle)
            return list_to_check, invalid_list

        incidences, invalid_incidences = check_list(incidences)
        emissions, invalid_emissions = check_list(emissions)
        azimuths, invalid_azimuths = check_list(azimuths)
        if invalid_incidences != [] or invalid_emissions != [] or invalid_azimuths != []:
            error_string = "Warning! Not all angles entered are valid.\n"
            if invalid_incidences != []:
                error_string += "\nInvalid incidences: " + str(invalid_incidences)
            if invalid_emissions != []:
                error_string += "\nInvalid emissions: " + str(invalid_emissions)
            if invalid_azimuths != []:
                error_string += "\nInvalid azimuths: " + str(invalid_azimuths)
            ErrorDialog(self.controller, "Warning!", error_string)

        return incidences, emissions, azimuths

    def select_tab(self):
        self.controller.view_notebook.select(self.tab.top)
