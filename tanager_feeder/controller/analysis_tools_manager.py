from tkinter import (
    Entry,
    Button,
    Label,
    Checkbutton,
    Frame,
    BOTH,
    EXTENDED,
    NORMAL,
    RIGHT,
    StringVar,
    LEFT,
    DISABLED,
    OptionMenu,
    IntVar,
    TclError,
)
import tkinter
from threading import Thread
import time

import numpy as np

from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.vertical_scrolled_dialog import VerticalScrolledDialog
from tanager_feeder import utils


class AnalysisToolsManager:
    def __init__(self, controller):
        self.tab = None
        self.controller = controller
        self.tk_format = utils.TkFormat(self.controller.config_info)

        self.analysis_dialog = None
        self.exclude_artifacts = IntVar()
        self.abs_val = IntVar()
        self.use_max_for_centers = IntVar()
        self.use_delta = IntVar()
        self.neg_depth = IntVar()

        self.normalize_entry = None
        self.right_zoom_entry = None
        self.right_zoom_entry2 = None
        self.left_zoom_entry = None
        self.left_zoom_entry2 = None
        self.left_slope_entry = None
        self.right_slope_entry = None
        self.slopes_listbox = None
        self.abs_val_check = None
        self.use_max_for_centers_check = None
        self.use_delta_check = None
        self.neg_depth_check = None
        self.exclude_artifacts_check = None
        self.extra_analysis_check_frame = None
        self.plot_slope_var = None
        self.offset_entry = None
        self.offset_sample_var = None
        self.plot_slope_menu = None
        self.plot_slope_button = None

        self.analyze_var = None

        self.outer_slope_frame = None
        self.slope_results_frame = None

    def show(self, tab):
        self.tab = tab
        self.tab.freeze()  # You have to finish dealing with this before, say, opening another analysis box.
        buttons = {
            "reset": {
                self.select_tab: [],
                self.tab.reset: [],
                self.uncheck_exclude_artifacts: [],
                self.disable_plot: [],
                # utils.thread_lift_widget: [],
            },
            "close": {},
        }
        self.analysis_dialog = VerticalScrolledDialog(
            self.controller, "Analyze Data", "", buttons=buttons, button_width=13
        )
        self.analysis_dialog.top.attributes("-topmost", True)



        outer_normalize_frame = Frame(
            self.analysis_dialog.interior, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15, highlightthickness=1
        )
        outer_normalize_frame.pack(expand=True, fill=BOTH)
        slope_title_label = Label(
            outer_normalize_frame, text="Normalize:", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        slope_title_label.pack()
        normalize_frame = Frame(outer_normalize_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15)
        normalize_frame.pack()

        normalize_label = Label(
            normalize_frame, text="Wavelength (nm):", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        self.normalize_entry = Entry(
            normalize_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        normalize_button = Button(
            normalize_frame,
            text="Apply",
            command=self.normalize,
            width=6,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        normalize_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        normalize_button.pack(side=RIGHT, padx=(10, 10))
        self.normalize_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        normalize_label.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_offset_frame = Frame(
            self.analysis_dialog.interior, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15, highlightthickness=1
        )
        outer_offset_frame.pack(expand=True, fill=BOTH)
        slope_title_label = Label(
            outer_offset_frame, text="Add offset to sample:", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        slope_title_label.pack(pady=(0, 15))
        offset_sample_frame = Frame(
            outer_offset_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        offset_sample_frame.pack()
        offset_sample_label = Label(
            offset_sample_frame, text="Sample: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        offset_sample_label.pack(side=LEFT)
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

        # pylint: disable = no-value-for-parameter
        offset_menu = OptionMenu(offset_sample_frame, self.offset_sample_var, *sample_names)
        offset_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
        offset_menu.pack(side=LEFT)
        offset_frame = Frame(outer_offset_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15)
        offset_frame.pack()
        offset_label = Label(offset_frame, text="Offset:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.offset_entry = Entry(
            offset_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        offset_button = Button(
            offset_frame,
            text="Apply",
            command=self.offset,
            width=6,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        offset_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        offset_button.pack(side=RIGHT, padx=(10, 10))
        self.offset_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        offset_label.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_outer_zoom_frame = Frame(
            self.analysis_dialog.interior, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15, highlightthickness=1
        )
        outer_outer_zoom_frame.pack(expand=True, fill=BOTH)

        zoom_title_frame = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg)
        zoom_title_frame.pack(pady=(5, 10))
        zoom_title_label = Label(
            zoom_title_frame, text="Adjust plot x and y limits:", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        zoom_title_label.pack(side=LEFT, pady=(0, 4))

        outer_zoom_frame = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        outer_zoom_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        zoom_frame = Frame(outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        zoom_frame.pack()

        zoom_label = Label(zoom_frame, text="x1:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_zoom_entry = Entry(
            zoom_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        zoom_label2 = Label(zoom_frame, text="x2:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry = Entry(
            zoom_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        zoom_button = Button(
            zoom_frame,
            text="Apply",
            command=self.apply_x,
            width=7,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        zoom_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        zoom_button.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label2.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_zoom_frame2 = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        outer_zoom_frame2.pack(expand=True, fill=BOTH, pady=(0, 10))
        zoom_frame2 = Frame(outer_zoom_frame2, bg=self.tk_format.bg, padx=self.tk_format.padx)
        zoom_frame2.pack()
        zoom_label3 = Label(zoom_frame2, text="y1:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_zoom_entry2 = Entry(
            zoom_frame2,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        zoom_label4 = Label(zoom_frame2, text="y2:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry2 = Entry(
            zoom_frame2,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        zoom_button2 = Button(
            zoom_frame2,
            text="Apply",
            command=self.apply_y,
            width=7,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        zoom_button2.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )

        zoom_button2.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry2.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label4.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry2.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label3.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_outer_slope_frame = Frame(
            self.analysis_dialog.interior, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15, highlightthickness=1
        )
        outer_outer_slope_frame.pack(expand=True, fill=BOTH)

        self.outer_slope_frame = Frame(outer_outer_slope_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        self.outer_slope_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        slope_title_frame = Frame(self.outer_slope_frame, bg=self.tk_format.bg)
        slope_title_frame.pack(pady=(5, 5))
        slope_title_label = Label(slope_title_frame, text="Analyze ", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        slope_title_label.pack(side=LEFT, pady=(0, 4))
        self.analyze_var = StringVar()
        self.analyze_var.set("slope")
        analyze_menu = OptionMenu(
            slope_title_frame,
            self.analyze_var,
            "slope",
            "band depth",
            "band center",
            "reflectance",
            # "reciprocity",
            "difference",
            command=self.disable_plot,
        )
        analyze_menu.configure(width=10, highlightbackground=self.tk_format.highlightbackgroundcolor)
        analyze_menu.pack(side=LEFT)

        # We'll put checkboxes for additional options into this frame at the time the user selects a given option (e.g.
        # select 'difference' from menu, add option to calculate differences based on absolute value
        self.extra_analysis_check_frame = Frame(self.outer_slope_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        self.extra_analysis_check_frame.pack()

        # Note that we are not packing this checkbutton yet.
        self.abs_val_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text=" Use absolute values for average differences",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.abs_val,
        )

        self.use_max_for_centers_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text=" If band max is more prominent than\nband min, use to find center.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.use_max_for_centers,
        )
        self.use_max_for_centers_check.select()

        self.use_delta_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text=" Center at max \u0394" + "R from continuum  \nrather than spectral min/max. ",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.use_delta,
        )
        self.use_delta_check.select()

        self.neg_depth_check = Checkbutton(
            self.extra_analysis_check_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text=" If band max is more prominent than \nband min, report negative depth.",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.neg_depth,
        )
        self.neg_depth_check.select()

        slope_frame = Frame(
            self.outer_slope_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, highlightthickness=0
        )
        slope_frame.pack(pady=(15, 0))

        slope_label = Label(slope_frame, text="x1:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_slope_entry = Entry(
            slope_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        slope_label_2 = Label(slope_frame, text="x2:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_slope_entry = Entry(
            slope_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        slope_button = Button(
            slope_frame,
            text="Calculate",
            command=self.calculate,
            width=7,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        slope_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )

        slope_button.pack(side=RIGHT, padx=(10, 10))
        self.right_slope_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        slope_label_2.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_slope_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        slope_label.pack(side=RIGHT, padx=self.tk_format.padx)
        self.slope_results_frame = Frame(self.outer_slope_frame, bg=self.tk_format.bg)
        self.slope_results_frame.pack(
            fill=BOTH, expand=True
        )  # We'll put a listbox with slope info in here later after calculating.

        outer_plot_slope_frame = Frame(outer_outer_slope_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=10)
        outer_plot_slope_frame.pack(expand=True, fill=BOTH)
        plot_slope_frame = Frame(outer_plot_slope_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        plot_slope_frame.pack(side=RIGHT)
        plot_slope_label = Label(
            plot_slope_frame, text="Plot as a function of", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        self.plot_slope_var = StringVar()
        self.plot_slope_var.set("e")
        self.plot_slope_menu = OptionMenu(plot_slope_frame, self.plot_slope_var, "e", "i", "g", "e,i", "theta", "az, e")
        self.plot_slope_menu.configure(width=2, highlightbackground=self.tk_format.highlightbackgroundcolor)
        self.plot_slope_button = Button(
            plot_slope_frame,
            text="Plot",
            command=self.plot,
            width=7,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        self.plot_slope_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            state=DISABLED,
        )
        self.plot_slope_button.pack(side=RIGHT, padx=(10, 10))
        self.plot_slope_menu.pack(side=RIGHT, padx=self.tk_format.padx)
        plot_slope_label.pack(side=RIGHT, padx=self.tk_format.padx)

        exclude_artifacts_frame = Frame(
            self.analysis_dialog.interior, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15, highlightthickness=1
        )
        exclude_artifacts_frame.pack(fill=BOTH, expand=True)

        self.exclude_artifacts_check = Checkbutton(
            exclude_artifacts_frame,
            selectcolor=self.tk_format.check_bg,
            fg=self.tk_format.textcolor,
            text=" Exclude data susceptible to artifacts\n (high g, 1000-1400 nm)  ",
            bg=self.tk_format.bg,
            pady=self.tk_format.pady,
            highlightthickness=0,
            variable=self.exclude_artifacts,
            # TODO: check if the comma is meant to be there in the lambda definition
            command=lambda x="foo",: self.tab.set_exclude_artifacts(self.exclude_artifacts.get()),
        )
        self.exclude_artifacts_check.pack()
        if self.tab.exclude_artifacts:
            self.exclude_artifacts_check.select()

        self.analysis_dialog.interior.configure(highlightthickness=1, highlightcolor="white")

    def calculate(self):
        try:
            self.controller.view_notebook.select(self.tab.top)
        except TclError:
            print("Error selecting tab in analysis_tools_manager.calculate().")
            print(self.tab)
            pass
        artifact_warning = False

        if self.analyze_var.get() == "slope":
            left, right, slopes, artifact_warning = self.tab.calculate_slopes(
                self.left_slope_entry.get(), self.right_slope_entry.get()
            )
            self.update_entries(left, right)
            self.populate_listbox(slopes)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta", "az, e"])

        elif self.analyze_var.get() == "band depth":
            left, right, depths, artifact_warning = self.tab.calculate_band_depths(
                self.left_slope_entry.get(),
                self.right_slope_entry.get(),
                self.neg_depth.get(),
                self.use_delta.get(),
            )
            self.update_entries(left, right)
            self.populate_listbox(depths)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta", "az, e"])

        elif self.analyze_var.get() == "band center":
            left, right, centers, artifact_warning = self.tab.calculate_band_centers(
                self.left_slope_entry.get(),
                self.right_slope_entry.get(),
                self.use_max_for_centers.get(),
                self.use_delta.get(),
            )
            self.update_entries(left, right)
            self.populate_listbox(centers)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta", "az, e"])

        elif self.analyze_var.get() == "reflectance":
            left, right, reflectance, artifact_warning = self.tab.calculate_avg_reflectance(
                self.left_slope_entry.get(), self.right_slope_entry.get()
            )
            self.update_entries(left, right)
            self.populate_listbox(reflectance)
            self.update_plot_menu(["e", "i", "g", "e,i", "theta", "az, e"])

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
            # pylint: disable = protected-access
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
            except (AttributeError, TclError):
                self.slopes_listbox = utils.ScrollableListbox(
                    self.slope_results_frame,
                    self.tk_format.bg,
                    self.tk_format.entry_background,
                    self.tk_format.listboxhighlightcolor,
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
        # TODO: plots not always fully updating
        #  (e.g. contour plot labels not showing up until you do a screen wiggle.


        # utils.thread_lift_widget(self.analysis_dialog.top)

    def normalize(self):
        self.select_tab()
        try:
            self.slopes_listbox.delete(0, "end")
            self.plot_slope_button.configure(state="disabled")
        except (AttributeError, TclError):
            pass
        self.tab.normalize(self.normalize_entry.get())
        # thread = Thread(target=utils.lift_widget, args=(self.analysis_dialog.top,))
        # thread.start()

    def offset(self):
        self.tab.offset(self.offset_sample_var.get(), self.offset_entry.get())

        # This doesn't work - it hangs between thread.start() and thread.join(). Likely because of calls to canvas.draw()
        # thread = Thread(target=self.tab.offset, args=(self.offset_sample_var.get(), self.offset_entry.get()))
        # thread.start()
        # thread.join()
        # utils.lift_widget(self.analysis_dialog.top)

    def remove_topmost(self):
        print("removing!!")
        self.analysis_dialog.top.attributes("-topmost", False)

    def apply_x(self):
        self.controller.view_notebook.select(self.tab.top)

        try:
            x1 = float(self.left_zoom_entry.get())
            x2 = float(self.right_zoom_entry.get())
            self.tab.adjust_x(x1, x2)
            # utils.lift_widget(self.analysis_dialog.top)
        except ValueError:
            # utils.lift_widget(self.analysis_dialog.top)
            ErrorDialog(
                self,
                title="Invalid Zoom Range",
                label="Error! Invalid x limits: " + self.left_zoom_entry.get() + ", " + self.right_zoom_entry.get(),
            )

    def apply_y(self):
        self.controller.view_notebook.select(self.tab.top)
        try:
            y1 = float(self.left_zoom_entry2.get())
            y2 = float(self.right_zoom_entry2.get())
            self.tab.adjust_y(y1, y2)
            # utils.lift_widget(self.analysis_dialog.top)
        except ValueError:
            # utils.lift_widget(self.analysis_dialog.top)
            ErrorDialog(
                self,
                title="Invalid Zoom Range",
                label="Error! Invalid y limits: " + self.left_zoom_entry2.get() + ", " + self.right_zoom_entry2.get(),
            )

    def uncheck_exclude_artifacts(self):
        self.exclude_artifacts.set(0)
        self.exclude_artifacts_check.deselect()
        # utils.lift_widget(self.analysis_dialog.top)

    def disable_plot(self, analyze_var="None"):
        try:
            self.slopes_listbox.delete(0, "end")
        except (AttributeError, TclError):
            pass
        self.plot_slope_button.configure(state="disabled")

        if analyze_var == "difference":
            self.analysis_dialog.frame.min_height = 850
            self.neg_depth_check.pack_forget()
            self.use_max_for_centers_check.pack_forget()
            self.use_delta_check.pack_forget()
            self.abs_val_check.pack()
            self.extra_analysis_check_frame.pack()

        elif analyze_var == "band center":
            self.analysis_dialog.frame.min_height = 1000
            self.neg_depth_check.pack_forget()
            self.abs_val_check.pack_forget()
            self.use_delta_check.pack_forget()
            self.use_max_for_centers_check.pack()
            self.use_delta_check.pack()
            self.extra_analysis_check_frame.pack()


        elif analyze_var == "band depth":
            self.analysis_dialog.frame.min_height = 1000
            self.abs_val_check.pack_forget()
            self.use_max_for_centers_check.pack_forget()
            self.use_delta_check.pack_forget()
            self.neg_depth_check.pack()
            self.use_delta_check.pack()
            self.extra_analysis_check_frame.pack()

        else:
            self.analysis_dialog.frame.min_height = 850
            self.abs_val_check.pack_forget()
            self.neg_depth_check.pack_forget()
            self.use_max_for_centers_check.pack_forget()
            self.use_delta_check.pack_forget()

            self.extra_analysis_check_frame.grid_propagate(0)
            self.extra_analysis_check_frame.configure(height=1)  # for some reason 0 doesn't work.
            self.extra_analysis_check_frame.pack()
            self.outer_slope_frame.pack()
        # utils.lift_widget(self.analysis_dialog.top)

    # def calculate_photometric_variability(self):
    #     photo_var = self.tab.calculate_photometric_variability(
    #         self.right_photo_var_entry.get(), self.left_photo_var_entry.get()
    #     )
    #     try:
    #         self.photo_var_listbox.delete(0, "end")
    #     except:
    #         self.photo_var_listbox = utils.ScrollableListbox(
    #             self.photo_var_results_frame,
    #             self.tk_format.bg,
    #             self.tk_format.entry_background,
    #             self.tk_format.listboxhighlightcolor,
    #             selectmode=EXTENDED,
    #         )
    #     for var in photo_var:
    #         self.photo_var_listbox.insert("end", var)
    #     self.photo_var_listbox.pack(fill=BOTH, expand=True)

    def select_tab(self):
        self.controller.view_notebook.select(self.tab.top)
        # utils.lift_widget(self.analysis_dialog.top)
