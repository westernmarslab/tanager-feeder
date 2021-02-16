from tkinter import Entry, Label, Checkbutton, Frame, LEFT, EXTENDED, END, IntVar

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder import utils


class EditPlotManager:
    def __init__(self, controller, tab, existing_sample_indices, sample_options, existing_geoms, current_title):
        self.view_notebook = controller.view_notebook
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

        self.edit_plot_dialog = Dialog(controller, "Edit Plot", "\nPlot title:", buttons=buttons)
        self.new_plot_title_entry = Entry(
            self.edit_plot_dialog.top,
            width=20,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.new_plot_title_entry.insert(0, current_title)
        self.new_plot_title_entry.pack()

        sample_label = Label(
            self.edit_plot_dialog.top, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="\nSamples:"
        )
        sample_label.pack(pady=(0, 10))
        self.plot_samples_listbox = utils.ScrollableListbox(
            self.edit_plot_dialog.top,
            self.bg,
            self.entry_background,
            self.listboxhighlightcolor,
            selectmode=EXTENDED,
        )

        self.geom_label = Label(
            self.edit_plot_dialog.top,
            padx=self.padx,
            pady=self.pady,
            bg=self.bg,
            fg=self.textcolor,
            text="\nEnter incidence and emission angles to plot,\nor leave blank to plot all:\n",
        )
        self.geom_label.pack()
        self.geom_frame = Frame(self.edit_plot_dialog.top)
        self.geom_frame.pack(padx=(20, 20), pady=(0, 10))
        self.i_label = Label(self.geom_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="i: ")
        self.i_label.pack(side=LEFT)
        self.i_entry = Entry(
            self.geom_frame,
            width=8,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        for i, incidence in enumerate(existing_geoms["i"]):
            if i == 0:
                self.i_entry.insert(0, str(incidence))
            else:
                self.i_entry.insert("end", "," + str(incidence))

        self.i_entry.pack(side=LEFT)

        self.e_label = Label(
            self.geom_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="    e: "
        )
        self.e_label.pack(side=LEFT)
        self.e_entry = Entry(
            self.geom_frame,
            width=8,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        for i, emission in enumerate(existing_geoms["e"]):
            if i == 0:
                self.e_entry.insert(0, str(emission))
            else:
                self.e_entry.insert("end", "," + str(emission))
        self.e_entry.pack(side=LEFT)

        self.az_label = Label(
            self.geom_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="    az: "
        )
        self.az_label.pack(side=LEFT)
        self.az_entry = Entry(
            self.geom_frame,
            width=8,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        for i, azimuth in enumerate(existing_geoms["az"]):
            if i == 0:
                self.az_entry.insert(0, str(azimuth))
            else:
                self.az_entry.insert("end", "," + str(azimuth))
        self.az_entry.pack(side=LEFT)
        print("packed")

        self.exclude_specular_frame = Frame(self.edit_plot_dialog.top, bg=self.bg, padx=self.padx, pady=self.pady)
        self.exclude_specular_frame.pack()
        self.exclude_specular = IntVar()
        self.exclude_specular_check = Checkbutton(
            self.exclude_specular_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text="  Exclude specular angles (+/-",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.exclude_specular,
        )
        self.exclude_specular_check.pack(side=LEFT)

        self.spec_tolerance_entry = Entry(
            self.exclude_specular_frame,
            width=4,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )

        self.spec_tolerance_entry.pack(side=LEFT)
        self.spec_tolerance_label = Label(
            self.exclude_specular_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text="\u00B0)"
        )
        self.spec_tolerance_label.pack(side=LEFT)

        if tab.exclude_specular:
            self.exclude_specular_check.select()
            self.spec_tolerance_entry.insert(0, tab.specularity_tolerance)

        for option in sample_options:
            self.plot_samples_listbox.insert(END, option)

        for i in existing_sample_indices:
            self.plot_samples_listbox.select_set(i)
        self.plot_samples_listbox.config(height=8)

    def check_angle_lists(self, incidences, emissions, azimuths):
        def check_list(angle_list):
            invalid_list = []
            angle_list = angle_list.split(",")
            if "None" in angle_list or "none" in angle_list:
                while "None" in angle_list:
                    angle_list.remove("None")
                while "none" in angle_list:
                    angle_list.remove("none")
                angle_list.append(None)
            if angle_list == [""]:
                angle_list = []
            for n, angle in enumerate(angle_list):
                if angle is not None:
                    try:
                        angle_list[n] = int(angle)
                    except:
                        invalid_list.append(angle)

            return angle_list, invalid_list

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
            ErrorDialog(self, "Warning!", error_string)

        return incidences, emissions, azimuths

    def select_tab(self):
        self.view_notebook.select(self.tab.top)
