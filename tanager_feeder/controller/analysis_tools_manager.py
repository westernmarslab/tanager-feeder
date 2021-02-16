from tkinter import Entry, Button, Label, Checkbutton, Frame, BOTH, EXTENDED, NORMAL, RIGHT, StringVar, LEFT, DISABLED, OptionMenu, IntVar
import tkinter
from threading import Thread

import numpy as np

from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.vertical_scrolled_dialog import VerticalScrolledDialog
from tanager_feeder import utils


class AnalysisToolsManager():
    def __init__(self, view_notebook, tab):
        self.tab = tab
        self.view_notebook = controller.view_notebook
        tab.freeze()  # You have to finish dealing with this before, say, opening another analysis box.
        buttons = {
            "reset": {self.select_tab: [], self.tab.reset: [], self.uncheck_exclude_artifacts: [], self.disable_plot: [], self.lift: []},
            "close": {},
        }

        self.analysis_dialog = VerticalScrolledDialog(controller, "Analyze Data", "", buttons=buttons, button_width=13)
        #         self.analysis_dialog.top.attributes('-topmost', True)

        self.outer_normalize_frame = Frame(
            self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15, highlightthickness=1
        )
        self.outer_normalize_frame.pack(expand=True, fill=BOTH)
        self.slope_title_label = Label(self.outer_normalize_frame, text="Normalize:", bg=self.bg, fg=self.textcolor)
        self.slope_title_label.pack()
        self.normalize_frame = Frame(self.outer_normalize_frame, bg=self.bg, padx=self.padx, pady=15)
        self.normalize_frame.pack()

        self.normalize_label = Label(self.normalize_frame, text="Wavelength (nm):", bg=self.bg, fg=self.textcolor)
        self.normalize_entry = Entry(
            self.normalize_frame,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.normalize_button = Button(
            self.normalize_frame,
            text="Apply",
            command=self.normalize,
            width=6,
            fg=self.buttontextcolor,
            bg=self.buttonbackgroundcolor,
            bd=self.bd,
        )
        self.normalize_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.normalize_button.pack(side=RIGHT, padx=(10, 10))
        self.normalize_entry.pack(side=RIGHT, padx=self.padx)
        self.normalize_label.pack(side=RIGHT, padx=self.padx)

        self.outer_offset_frame = Frame(
            self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15, highlightthickness=1
        )
        self.outer_offset_frame.pack(expand=True, fill=BOTH)
        self.slope_title_label = Label(
            self.outer_offset_frame, text="Add offset to sample:", bg=self.bg, fg=self.textcolor
        )
        self.slope_title_label.pack(pady=(0, 15))
        self.offset_sample_frame = Frame(self.outer_offset_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        self.offset_sample_frame.pack()
        self.offset_sample_label = Label(self.offset_sample_frame, text="Sample: ", bg=self.bg, fg=self.textcolor)
        self.offset_sample_label.pack(side=LEFT)
        self.offset_sample_var = StringVar()
        sample_names = []
        repeats = False
        max_len = 0
        for sample in self.tab.samples:
            if sample.name in sample_names:
                repeats = True
            else:
                sample_names.append(sample.name)
                max_len = np.max([max_len, len(sample.name)])
        if repeats:
            sample_names = []
            for sample in self.tab.samples:
                sample_names.append(sample.title + ": " + sample.name)
                max_len = np.max([max_len, len(sample_names[-1])])
        self.offset_sample_var.set(sample_names[0])
        self.offset_menu = OptionMenu(self.offset_sample_frame, self.offset_sample_var, *sample_names)
        self.offset_menu.configure(width=max_len, highlightbackground=self.highlightbackgroundcolor)
        self.offset_menu.pack(side=LEFT)
        self.offset_frame = Frame(self.outer_offset_frame, bg=self.bg, padx=self.padx, pady=15)
        self.offset_frame.pack()
        self.offset_label = Label(self.offset_frame, text="Offset:", bg=self.bg, fg=self.textcolor)
        self.offset_entry = Entry(
            self.offset_frame,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.offset_button = Button(
            self.offset_frame,
            text="Apply",
            command=self.offset,
            width=6,
            fg=self.buttontextcolor,
            bg=self.buttonbackgroundcolor,
            bd=self.bd,
        )
        self.offset_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.offset_button.pack(side=RIGHT, padx=(10, 10))
        self.offset_entry.pack(side=RIGHT, padx=self.padx)
        self.offset_label.pack(side=RIGHT, padx=self.padx)

        self.outer_outer_zoom_frame = Frame(
            self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15, highlightthickness=1
        )
        self.outer_outer_zoom_frame.pack(expand=True, fill=BOTH)

        self.zoom_title_frame = Frame(self.outer_outer_zoom_frame, bg=self.bg)
        self.zoom_title_frame.pack(pady=(5, 10))
        self.zoom_title_label = Label(
            self.zoom_title_frame, text="Adjust plot x and y limits:", bg=self.bg, fg=self.textcolor
        )
        self.zoom_title_label.pack(side=LEFT, pady=(0, 4))

        self.outer_zoom_frame = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
        self.outer_zoom_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        self.zoom_frame = Frame(self.outer_zoom_frame, bg=self.bg, padx=self.padx)
        self.zoom_frame.pack()

        self.zoom_label = Label(self.zoom_frame, text="x1:", bg=self.bg, fg=self.textcolor)
        self.left_zoom_entry = Entry(
            self.zoom_frame,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.zoom_label2 = Label(self.zoom_frame, text="x2:", bg=self.bg, fg=self.textcolor)
        self.right_zoom_entry = Entry(
            self.zoom_frame,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.zoom_button = Button(
            self.zoom_frame,
            text="Apply",
            command=self.apply_x,
            width=7,
            fg=self.buttontextcolor,
            bg=self.buttonbackgroundcolor,
            bd=self.bd,
        )
        self.zoom_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )
        self.zoom_button.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry.pack(side=RIGHT, padx=self.padx)
        self.zoom_label2.pack(side=RIGHT, padx=self.padx)
        self.left_zoom_entry.pack(side=RIGHT, padx=self.padx)
        self.zoom_label.pack(side=RIGHT, padx=self.padx)

        self.outer_zoom_frame2 = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
        self.outer_zoom_frame2.pack(expand=True, fill=BOTH, pady=(0, 10))
        self.zoom_frame2 = Frame(self.outer_zoom_frame2, bg=self.bg, padx=self.padx)
        self.zoom_frame2.pack()
        self.zoom_label3 = Label(self.zoom_frame2, text="y1:", bg=self.bg, fg=self.textcolor)
        self.left_zoom_entry2 = Entry(
            self.zoom_frame2,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.zoom_label4 = Label(self.zoom_frame2, text="y2:", bg=self.bg, fg=self.textcolor)
        self.right_zoom_entry2 = Entry(
            self.zoom_frame2,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.zoom_button2 = Button(
            self.zoom_frame2,
            text="Apply",
            command=self.apply_y,
            width=7,
            fg=self.buttontextcolor,
            bg=self.buttonbackgroundcolor,
            bd=self.bd,
        )
        self.zoom_button2.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )

        self.zoom_button2.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry2.pack(side=RIGHT, padx=self.padx)
        self.zoom_label4.pack(side=RIGHT, padx=self.padx)
        self.left_zoom_entry2.pack(side=RIGHT, padx=self.padx)
        self.zoom_label3.pack(side=RIGHT, padx=self.padx)

        self.outer_outer_slope_frame = Frame(
            self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15, highlightthickness=1
        )
        self.outer_outer_slope_frame.pack(expand=True, fill=BOTH)

        self.outer_slope_frame = Frame(self.outer_outer_slope_frame, bg=self.bg, padx=self.padx)
        self.outer_slope_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        self.slope_title_frame = Frame(self.outer_slope_frame, bg=self.bg)
        self.slope_title_frame.pack(pady=(5, 5))
        self.slope_title_label = Label(self.slope_title_frame, text="Analyze ", bg=self.bg, fg=self.textcolor)
        self.slope_title_label.pack(side=LEFT, pady=(0, 4))
        self.analyze_var = StringVar()
        self.analyze_var.set("slope")
        self.analyze_menu = OptionMenu(
            self.slope_title_frame,
            self.analyze_var,
            "slope",
            "band depth",
            "band center",
            "reflectance",
            "reciprocity",
            "difference",
            command=self.disable_plot,
        )
        self.analyze_menu.configure(width=10, highlightbackground=self.highlightbackgroundcolor)
        self.analyze_menu.pack(side=LEFT)

        # We'll put checkboxes for additional options into this frame at the time the user selects a given option (e.g.
        # select 'difference' from menu, add option to calculate differences based on absolute value
        self.extra_analysis_check_frame = Frame(self.outer_slope_frame, bg=self.bg, padx=self.padx)
        self.extra_analysis_check_frame.pack()
        self.abs_val = IntVar()
        # Note that we are not packing this checkbutton yet.
        self.abs_val_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text=" Use absolute values for average differences",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.abs_val,
        )

        self.use_max_for_centers = IntVar()
        self.use_max_for_centers_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text=" If band max is more prominent than\nband min, use to find center.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.use_max_for_centers,
        )
        self.use_max_for_centers_check.select()

        self.use_delta = IntVar()
        self.use_delta_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text=" Center at max \u0394" + "R from continuum  \nrather than spectral min/max. ",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.use_delta,
        )
        self.use_delta_check.select()

        self.neg_depth = IntVar()
        self.neg_depth_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text=" If band max is more prominent than \nband min, report negative depth.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.neg_depth,
        )
        self.neg_depth_check.select()

        self.slope_frame = Frame(self.outer_slope_frame, bg=self.bg, padx=self.padx, highlightthickness=0)
        self.slope_frame.pack(pady=(15, 0))

        self.slope_label = Label(self.slope_frame, text="x1:", bg=self.bg, fg=self.textcolor)
        self.left_slope_entry = Entry(
            self.slope_frame,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.slope_label_2 = Label(self.slope_frame, text="x2:", bg=self.bg, fg=self.textcolor)
        self.right_slope_entry = Entry(
            self.slope_frame,
            width=7,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.slope_button = Button(
            self.slope_frame,
            text="Calculate",
            command=self.calculate,
            width=7,
            fg=self.buttontextcolor,
            bg=self.buttonbackgroundcolor,
            bd=self.bd,
        )
        self.slope_button.config(
            fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor, bg=self.buttonbackgroundcolor
        )

        self.slope_button.pack(side=RIGHT, padx=(10, 10))
        self.right_slope_entry.pack(side=RIGHT, padx=self.padx)
        self.slope_label_2.pack(side=RIGHT, padx=self.padx)
        self.left_slope_entry.pack(side=RIGHT, padx=self.padx)
        self.slope_label.pack(side=RIGHT, padx=self.padx)
        self.slope_results_frame = Frame(self.outer_slope_frame, bg=self.bg)
        self.slope_results_frame.pack(
            fill=BOTH, expand=True
        )  # We'll put a listbox with slope info in here later after calculating.

        self.outer_plot_slope_frame = Frame(self.outer_outer_slope_frame, bg=self.bg, padx=self.padx, pady=10)
        self.outer_plot_slope_frame.pack(expand=True, fill=BOTH)
        self.plot_slope_frame = Frame(self.outer_plot_slope_frame, bg=self.bg, padx=self.padx)
        self.plot_slope_frame.pack(side=RIGHT)
        self.plot_slope_label = Label(
            self.plot_slope_frame, text="Plot as a function of", bg=self.bg, fg=self.textcolor
        )
        self.plot_slope_var = StringVar()
        self.plot_slope_var.set("e")
        self.plot_slope_menu = OptionMenu(self.plot_slope_frame, self.plot_slope_var, "e", "i", "g", "e,i", "theta")
        self.plot_slope_menu.configure(width=2, highlightbackground=self.highlightbackgroundcolor)
        self.plot_slope_button = Button(
            self.plot_slope_frame,
            text="Plot",
            command=self.plot,
            width=7,
            fg=self.buttontextcolor,
            bg=self.buttonbackgroundcolor,
            bd=self.bd,
        )
        self.plot_slope_button.config(
            fg=self.buttontextcolor,
            highlightbackground=self.highlightbackgroundcolor,
            bg=self.buttonbackgroundcolor,
            state=DISABLED,
        )
        self.plot_slope_button.pack(side=RIGHT, padx=(10, 10))
        self.plot_slope_menu.pack(side=RIGHT, padx=self.padx)
        self.plot_slope_label.pack(side=RIGHT, padx=self.padx)

        self.exclude_artifacts_frame = Frame(
            self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15, highlightthickness=1
        )
        self.exclude_artifacts_frame.pack(fill=BOTH, expand=True)
        self.exclude_artifacts = IntVar()
        self.exclude_artifacts_check = Checkbutton(
            self.exclude_artifacts_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text=" Exclude data susceptible to artifacts\n (high g, 1000-1400 nm)  ",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.exclude_artifacts,
            command=lambda x="foo",: self.tab.set_exclude_artifacts(self.exclude_artifacts.get()),
        )
        self.exclude_artifacts_check.pack()
        if self.tab.exclude_artifacts:
            self.exclude_artifacts_check.select()

        self.analysis_dialog.interior.configure(highlightthickness=1, highlightcolor="white")

    def calculate(self):
        self.view_notebook.select(self.self.tab.top)
        artifact_warning = False

        if self.analyze_var.get() == "slope":
            left, right, slopes, artifact_warning = self.self.tab.calculate_slopes(
                self.left_slope_entry.get(), self.right_slope_entry.get()
            )
            self.update_entries(left, right)
            self.populate_listbox(slopes)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta"])

        elif self.analyze_var.get() == "band depth":
            left, right, depths, artifact_warning = self.tab.calculate_band_depths(
                self.left_slope_entry.get(),
                self.right_slope_entry.get(),
                self.neg_depth.get(),
                self.use_delta.get(),
            )
            self.update_entries(left, right)
            self.populate_listbox(depths)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta"])

        elif self.analyze_var.get() == "band center":
            left, right, centers, artifact_warning = self.tab.calculate_band_centers(
                self.left_slope_entry.get(),
                self.right_slope_entry.get(),
                self.use_max_for_centers.get(),
                self.use_delta.get(),
            )
            self.update_entries(left, right)
            self.populate_listbox(centers)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta"])

        elif self.analyze_var.get() == "reflectance":
            left, right, reflectance, artifact_warning = self.tab.calculate_avg_reflectance(
                self.left_slope_entry.get(), self.right_slope_entry.get()
            )
            self.update_entries(left, right)
            self.populate_listbox(reflectance)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta"])

        elif self.analyze_var.get() == "reciprocity":
            left, right, reciprocity, artifact_warning = self.tab.calculate_reciprocity(
                self.left_slope_entry.get(), self.right_slope_entry.get()
            )
            self.update_entries(left, right)
            self.populate_listbox(reciprocity)
            self.update_plot_menu(["e", "i", "g", "e,i"])

        elif self.analyze_var.get() == "difference":
            left, right, error, artifact_warning = self.tab.calculate_error(
                self.left_slope_entry.get(), self.right_slope_entry.get(), self.abs_val.get()
            )
            # Tab validates left and right values. If they are no good, put in min and max wavelengths available.
            self.update_entries(left, right)
            self.populate_listbox(error)
            self.update_plot_menu(["\u03bb", "e,i"])

        if artifact_warning:
            ErrorDialog(
                self, "Warning", "Warning: Excluding data potentially\ninfluenced by artifacts from 1000-1400 nm."
            )

        self.analysis_dialog.min_height = 1000
        self.analysis_dialog.update()

    def update_plot_menu(self, plot_options):
        self.plot_slope_var.set(plot_options[0])
        self.plot_slope_menu["menu"].delete(0, "end")

        # Insert list of new options (tk._setit hooks them up to var)
        max_len = len(plot_options[0])
        for option in plot_options:
            max_len = np.max([max_len, len(option)])
            self.plot_slope_menu["menu"].add_command(label=option, command=tkinter._setit(self.plot_slope_var, option))
        self.plot_slope_menu.configure(width=max_len)

    def update_entries(self, left, right):
        self.left_slope_entry.delete(0, "end")
        self.left_slope_entry.insert(0, str(left))
        self.right_slope_entry.delete(0, "end")
        self.right_slope_entry.insert(0, str(right))

    def populate_listbox(self, results):
        if len(results) > 0:
            self.slope_results_frame.pack(fill=BOTH, expand=True, pady=(10, 10))
            try:
                self.slopes_listbox.delete(0, "end")
            except:
                self.slopes_listbox = utils.ScrollableListbox(
                    self.slope_results_frame,
                    self.bg,
                    self.entry_background,
                    self.listboxhighlightcolor,
                    selectmode=EXTENDED,
                )
                self.slopes_listbox.configure(height=8)
            for result in results:
                self.slopes_listbox.insert("end", result)
            self.slopes_listbox.pack(fill=BOTH, expand=True)
            self.plot_slope_button.configure(state=NORMAL)

    def plot(self):
        if self.analyze_var.get() == "slope":
            self.tab.plot_slopes(self.plot_slope_var.get())
        elif self.analyze_var.get() == "band depth":
            self.tab.plot_band_depths(self.plot_slope_var.get())
        elif self.analyze_var.get() == "band center":
            self.tab.plot_band_centers(self.plot_slope_var.get())
        elif self.analyze_var.get() == "reflectance":
            self.tab.plot_avg_reflectance(self.plot_slope_var.get())
        elif self.analyze_var.get() == "reciprocity":
            self.tab.plot_reciprocity(self.plot_slope_var.get())
        elif self.analyze_var.get() == "difference":
            new = self.tab.plot_error(self.plot_slope_var.get())

        if self.plot_slope_var.get() == "\u03bb":
            x1 = float(self.left_slope_entry.get())
            x2 = float(self.right_slope_entry.get())
            new.adjust_x(x1, x2)

        self.thread_lift_widget(self.analysis_dialog.top)

    def normalize(self):
        self.select_tab()
        try:
            self.slopes_listbox.delete(0, "end")
            self.plot_slope_button.configure(state="disabled")
        except:
            pass
        self.tab.normalize(self.normalize_entry.get())
        thread = Thread(target=self.lift_widget, args=(self.analysis_dialog.top,))
        thread.start()

    def offset(self):
        self.tab.offset(self.offset_sample_var.get(), self.offset_entry.get())
        thread = Thread(target=self.lift_widget, args=(self.analysis_dialog.top,))
        thread.start()

    def apply_x(self):
        self.view_notebook.select(self.tab.top)

        try:
            x1 = float(self.left_zoom_entry.get())
            x2 = float(self.right_zoom_entry.get())
            self.tab.adjust_x(x1, x2)
            self.lift_widget(self.analysis_dialog.top)
        except:
            self.lift_widget(self.analysis_dialog.top)
            ErrorDialog(
                self,
                title="Invalid Zoom Range",
                label="Error! Invalid x limits: " + self.left_zoom_entry.get() + ", " + self.right_zoom_entry.get(),
            )

    def apply_y(self):
        self.view_notebook.select(self.tab.top)
        try:
            y1 = float(self.left_zoom_entry2.get())
            y2 = float(self.right_zoom_entry2.get())
            self.tab.adjust_y(y1, y2)
            self.lift_widget(self.analysis_dialog.top)
        except:
            self.lift_widget(self.analysis_dialog.top)
            ErrorDialog(
                self,
                title="Invalid Zoom Range",
                label="Error! Invalid y limits: "
                      + self.left_zoom_entry2.get()
                      + ", "
                      + self.right_zoom_entry2.get(),
            )

    def uncheck_exclude_artifacts(self):
        self.exclude_artifacts.set(0)
        self.exclude_artifacts_check.deselect()
        self.lift_widget(self.analysis_dialog.top)

    def disable_plot(self, analyze_var="None"):
        try:
            self.slopes_listbox.delete(0, "end")
        except:
            pass
        self.plot_slope_button.configure(state="disabled")

        if analyze_var == "difference":
            self.neg_depth_check.pack_forget()
            self.use_max_for_centers_check.pack_forget()
            self.use_delta_check.pack_forget()
            self.abs_val_check.pack()
            self.extra_analysis_check_frame.pack()

        elif analyze_var == "band center":
            self.neg_depth_check.pack_forget()
            self.abs_val_check.pack_forget()
            self.use_delta_check.pack_forget()
            self.use_max_for_centers_check.pack()
            self.use_delta_check.pack()
            self.extra_analysis_check_frame.pack()

        elif analyze_var == "band depth":
            self.abs_val_check.pack_forget()
            self.use_max_for_centers_check.pack_forget()
            self.use_delta_check.pack_forget()
            self.neg_depth_check.pack()
            self.use_delta_check.pack()
            self.extra_analysis_check_frame.pack()

        else:
            self.abs_val_check.pack_forget()
            self.neg_depth_check.pack_forget()
            self.use_max_for_centers_check.pack_forget()
            self.use_delta_check.pack_forget()

            self.extra_analysis_check_frame.grid_propagate(0)
            self.extra_analysis_check_frame.configure(height=1)  # for some reason 0 doesn't work.
            self.extra_analysis_check_frame.pack()
            self.outer_slope_frame.pack()

        self.lift_widget(self.analysis_dialog.top)

    def calculate_photometric_variability(self):
        photo_var = self.tab.calculate_photometric_variability(
            self.right_photo_var_entry.get(), self.left_photo_var_entry.get()
        )
        try:
            self.photo_var_listbox.delete(0, "end")
        except:
            self.photo_var_listbox = utils.ScrollableListbox(
                self.photo_var_results_frame,
                self.bg,
                self.entry_background,
                self.listboxhighlightcolor,
                selectmode=EXTENDED,
            )
        for var in photo_var:
            self.photo_var_listbox.insert("end", var)
        self.photo_var_listbox.pack(fill=BOTH, expand=True)

    def select_tab(self):
        self.view_notebook.select(self.tab.top)
        self.lift_widget(self.analysis_dialog.top)


    def lift(self):
        self.thread_lift_widget(self.analysis_dialog.top)