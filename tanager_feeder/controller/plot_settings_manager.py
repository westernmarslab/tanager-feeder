from tkinter import (
    Entry,
    Button,
    Label,
    Frame,
    BOTH,
    RIGHT,
    StringVar,
    LEFT,
    OptionMenu,
)

import numpy as np

from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.custom_color_dialog import CustomColorDialog
from tanager_feeder.dialogs.vertical_scrolled_dialog import VerticalScrolledDialog
from tanager_feeder import utils


class PlotSettingsManager:
    def __init__(self, controller):
        self.controller = controller
        self.tk_format = utils.TkFormat(controller.config_info)

        self.tab = None
        self.plot_settings_dialog = None
        self.custom_color_dialog = None

        self.color_sample_var = StringVar()
        self.color_color_var = StringVar()
        self.linestyle_sample_var = StringVar()
        self.linestyle_linestyle_var = StringVar()
        self.markerstyle_sample_var = StringVar()
        self.markerstyle_markerstyle_var = StringVar()
        self.legend_legend_var = StringVar()

        self.left_zoom_entry_x = None
        self.right_zoom_entry_x = None
        self.left_zoom_entry_y = None
        self.right_zoom_entry_y = None
        self.left_zoom_entry_z = None
        self.right_zoom_entry_z = None

        self.title_entry = None

    def show(self, tab):
        # If the user already has dialogs open for editing the plot, close the extras to avoid confusion.
        self.tab = tab
        self.tab.freeze()  # You have to finish dealing with this before, say, opening another analysis box.
        buttons = {"close": {}}

        self.plot_settings_dialog = VerticalScrolledDialog(
            self.controller, "Plot Settings", "", buttons=buttons, button_width=13, min_height=715, width=360
        )
        self.plot_settings_dialog.top.wm_geometry("360x600")

        outer_title_frame = Frame(
            self.plot_settings_dialog.interior,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=15,
            highlightthickness=1,
        )
        outer_title_frame.pack(expand=True, fill=BOTH)

        title_frame = Frame(outer_title_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15)
        title_frame.pack(fill=BOTH, expand=True)

        title_label = Label(
            title_frame, text="Plot title:", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        self.title_entry = Entry(
            title_frame,
            width=20,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        title_button = Button(
            title_frame,
            text="Apply",
            command=self.set_title,
            width=6,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        title_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        title_button.pack(side=RIGHT, padx=(10, 20))
        self.title_entry.pack(side=RIGHT, padx=self.tk_format.padx)
        title_label.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_outer_zoom_frame = Frame(
            self.plot_settings_dialog.interior,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=15,
            highlightthickness=1,
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
        self.left_zoom_entry_x = Entry(
            zoom_frame,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        zoom_label2 = Label(zoom_frame, text="x2:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry_x = Entry(
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
        self.right_zoom_entry_x.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label2.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry_x.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_zoom_frame2 = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
        outer_zoom_frame2.pack(expand=True, fill=BOTH, pady=(0, 10))
        zoom_frame2 = Frame(outer_zoom_frame2, bg=self.tk_format.bg, padx=self.tk_format.padx)
        zoom_frame2.pack()
        zoom_label3 = Label(zoom_frame2, text="y1:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.left_zoom_entry_y = Entry(
            zoom_frame2,
            width=7,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        zoom_label4 = Label(zoom_frame2, text="y2:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.right_zoom_entry_y = Entry(
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
        self.right_zoom_entry_y.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label4.pack(side=RIGHT, padx=self.tk_format.padx)
        self.left_zoom_entry_y.pack(side=RIGHT, padx=self.tk_format.padx)
        zoom_label3.pack(side=RIGHT, padx=self.tk_format.padx)

        if self.tab.plot.x_axis == "contour":
            outer_zoom_frame_z = Frame(outer_outer_zoom_frame, bg=self.tk_format.bg, padx=self.tk_format.padx)
            outer_zoom_frame_z.pack(expand=True, fill=BOTH, pady=(0, 10))
            zoom_frame_z = Frame(outer_zoom_frame_z, bg=self.tk_format.bg, padx=self.tk_format.padx)
            zoom_frame_z.pack()
            zoom_label_z1 = Label(zoom_frame_z, text="z1:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
            self.left_zoom_entry_z = Entry(
                zoom_frame_z,
                width=7,
                bd=self.tk_format.bd,
                bg=self.tk_format.entry_background,
                selectbackground=self.tk_format.selectbackground,
                selectforeground=self.tk_format.selectforeground,
            )
            zoom_label_z2 = Label(zoom_frame_z, text="z2:", bg=self.tk_format.bg, fg=self.tk_format.textcolor)
            self.right_zoom_entry_z = Entry(
                zoom_frame_z,
                width=7,
                bd=self.tk_format.bd,
                bg=self.tk_format.entry_background,
                selectbackground=self.tk_format.selectbackground,
                selectforeground=self.tk_format.selectforeground,
            )
            zoom_button_z = Button(
                zoom_frame_z,
                text="Apply",
                command=self.apply_z,
                width=7,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
            zoom_button_z.config(
                fg=self.tk_format.buttontextcolor,
                highlightbackground=self.tk_format.highlightbackgroundcolor,
                bg=self.tk_format.buttonbackgroundcolor,
            )

            zoom_button_z.pack(side=RIGHT, padx=(10, 10))
            self.right_zoom_entry_z.pack(side=RIGHT, padx=self.tk_format.padx)
            zoom_label_z2.pack(side=RIGHT, padx=self.tk_format.padx)
            self.left_zoom_entry_z.pack(side=RIGHT, padx=self.tk_format.padx)
            zoom_label_z1.pack(side=RIGHT, padx=self.tk_format.padx)

        outer_color_frame = Frame(
            self.plot_settings_dialog.interior,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=15,
            highlightthickness=1,
        )
        outer_color_frame.pack(expand=True, fill=BOTH)
        color_label = Label(
            outer_color_frame, text="Color settings", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        color_label.pack()

        color_frame = Frame(outer_color_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15)
        color_frame.pack(fill=BOTH, expand=True)
        color_sample_frame = Frame(color_frame, bg=self.tk_format.bg, padx=30, pady=0)
        color_sample_frame.pack(fill=BOTH, expand=True)

        color_sample_label = Label(
            color_sample_frame, text="Sample: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        color_sample_label.pack(side=LEFT)

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
        self.color_sample_var.set(sample_names[0])

        # pylint: disable = no-value-for-parameter
        color_menu = OptionMenu(color_sample_frame, self.color_sample_var, *sample_names)
        color_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
        color_menu.pack(side=LEFT)

        color_color_frame = Frame(color_frame, bg=self.tk_format.bg, padx=40, pady=0)
        color_color_frame.pack(fill=BOTH, expand=True)
        color_sample_label = Label(
            color_color_frame, text="Color: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        color_sample_label.pack(side=LEFT)

        color_names = self.tab.plot.color_names

        self.color_color_var.set(color_names[0])

        # pylint: disable = no-value-for-parameter
        color_menu = OptionMenu(color_color_frame, self.color_color_var, *color_names)
        color_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
        color_menu.pack(side=LEFT)
        color_button = Button(
            color_frame,
            text="Apply",
            command=self.set_color,
            width=6,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        color_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        color_button.pack()

        if self.tab.plot.lines_drawn:
            outer_linestyle_frame = Frame(
                self.plot_settings_dialog.interior,
                bg=self.tk_format.bg,
                padx=self.tk_format.padx,
                pady=15,
                highlightthickness=1,
            )
            outer_linestyle_frame.pack(expand=True, fill=BOTH)
            linestyle_label = Label(
                outer_linestyle_frame, text="Linestyle settings", bg=self.tk_format.bg, fg=self.tk_format.textcolor
            )
            linestyle_label.pack()

            linestyle_frame = Frame(
                outer_linestyle_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15
            )
            linestyle_frame.pack(fill=BOTH, expand=True)
            linestyle_sample_frame = Frame(linestyle_frame, bg=self.tk_format.bg, padx=30, pady=0)
            linestyle_sample_frame.pack(fill=BOTH, expand=True)

            linestyle_sample_label = Label(
                linestyle_sample_frame, text="Sample: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
            )
            linestyle_sample_label.pack(side=LEFT)

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
            self.linestyle_sample_var.set(sample_names[0])

            # pylint: disable = no-value-for-parameter
            linestyle_menu = OptionMenu(linestyle_sample_frame, self.linestyle_sample_var, *sample_names)
            linestyle_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
            linestyle_menu.pack(side=LEFT)

            linestyle_linestyle_frame = Frame(linestyle_frame, bg=self.tk_format.bg, padx=44, pady=0)
            linestyle_linestyle_frame.pack(fill=BOTH, expand=True)
            linestyle_sample_label = Label(
                linestyle_linestyle_frame, text="Style: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
            )
            linestyle_sample_label.pack(side=LEFT)

            linestyle_names = ["Solid", "Dash", "Dot", "Dot-dash"]

            self.linestyle_linestyle_var.set(linestyle_names[0])

            # pylint: disable = no-value-for-parameter
            linestyle_menu = OptionMenu(
                linestyle_linestyle_frame, self.linestyle_linestyle_var, *linestyle_names
            )
            linestyle_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
            linestyle_menu.pack(side=LEFT)
            linestyle_button = Button(
                linestyle_frame,
                text="Apply",
                command=self.set_linestyle,
                width=6,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
            linestyle_button.config(
                fg=self.tk_format.buttontextcolor,
                highlightbackground=self.tk_format.highlightbackgroundcolor,
                bg=self.tk_format.buttonbackgroundcolor,
            )
            linestyle_button.pack()

        if self.tab.plot.markers_drawn:
            outer_markerstyle_frame = Frame(
                self.plot_settings_dialog.interior,
                bg=self.tk_format.bg,
                padx=self.tk_format.padx,
                pady=15,
                highlightthickness=1,
            )
            outer_markerstyle_frame.pack(expand=True, fill=BOTH)
            markerstyle_label = Label(
                outer_markerstyle_frame,
                text="Markerstyle settings",
                bg=self.tk_format.bg,
                fg=self.tk_format.textcolor,
            )
            markerstyle_label.pack()

            markerstyle_frame = Frame(
                outer_markerstyle_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15
            )
            markerstyle_frame.pack(fill=BOTH, expand=True)
            markerstyle_sample_frame = Frame(markerstyle_frame, bg=self.tk_format.bg, padx=30, pady=0)
            markerstyle_sample_frame.pack(fill=BOTH, expand=True)

            markerstyle_sample_label = Label(
                markerstyle_sample_frame, text="Sample: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
            )
            markerstyle_sample_label.pack(side=LEFT)

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
            self.markerstyle_sample_var.set(sample_names[0])

            # pylint: disable = no-value-for-parameter
            markerstyle_menu = OptionMenu(
                markerstyle_sample_frame, self.markerstyle_sample_var, *sample_names
            )
            markerstyle_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
            markerstyle_menu.pack(side=LEFT)

            markerstyle_markerstyle_frame = Frame(markerstyle_frame, bg=self.tk_format.bg, padx=44, pady=0)
            markerstyle_markerstyle_frame.pack(fill=BOTH, expand=True)
            markerstyle_sample_label = Label(
                markerstyle_markerstyle_frame, text="Style: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
            )
            markerstyle_sample_label.pack(side=LEFT)

            markerstyle_names = ["Circle", "X", "Diamond", "Triangle"]

            self.markerstyle_markerstyle_var.set(markerstyle_names[0])

            # pylint: disable = no-value-for-parameter
            markerstyle_menu = OptionMenu(
                markerstyle_markerstyle_frame, self.markerstyle_markerstyle_var, *markerstyle_names
            )
            markerstyle_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
            markerstyle_menu.pack(side=LEFT)
            markerstyle_button = Button(
                markerstyle_frame,
                text="Apply",
                command=self.set_markerstyle,
                width=6,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
            markerstyle_button.config(
                fg=self.tk_format.buttontextcolor,
                highlightbackground=self.tk_format.highlightbackgroundcolor,
                bg=self.tk_format.buttonbackgroundcolor,
            )
            markerstyle_button.pack()

        outer_legend_frame = Frame(
            self.plot_settings_dialog.interior,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=15,
            highlightthickness=1,
        )
        outer_legend_frame.pack(expand=True, fill=BOTH)

        legend_frame = Frame(outer_legend_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=15)
        legend_frame.pack(fill=BOTH, expand=True)

        legend_legend_frame = Frame(legend_frame, bg=self.tk_format.bg, padx=20, pady=0)
        legend_legend_frame.pack(fill=BOTH, expand=True)
        legend_sample_label = Label(
            legend_legend_frame, text="Legend style: ", bg=self.tk_format.bg, fg=self.tk_format.textcolor
        )
        legend_sample_label.pack(side=LEFT)

        legend_names = ["Full list", "Gradient"]

        self.legend_legend_var.set(legend_names[0])

        # pylint: disable = no-value-for-parameter
        legend_menu = OptionMenu(legend_legend_frame, self.legend_legend_var, *legend_names)
        legend_menu.configure(width=max_len, highlightbackground=self.tk_format.highlightbackgroundcolor)
        legend_menu.pack(side=LEFT)
        legend_button = Button(
            legend_legend_frame,
            text="Apply",
            command=self.set_legend,
            width=6,
            fg=self.tk_format.buttontextcolor,
            bg=self.tk_format.buttonbackgroundcolor,
            bd=self.tk_format.bd,
        )
        legend_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        legend_button.pack(side=LEFT, padx=(5, 5), pady=(5, 3))


    def select_tab(self):
        self.controller.view_notebook.select(self.tab.top)
        utils.lift_widget(self.plot_settings_dialog.top)

    def apply_x(self):
        self.controller.view_notebook.select(self.tab.top)

        try:
            x1 = float(self.left_zoom_entry_x.get())
            x2 = float(self.right_zoom_entry_x.get())
            self.tab.adjust_x(x1, x2)
            utils.lift_widget(self.plot_settings_dialog.top)
        except ValueError:
            utils.lift_widget(self.plot_settings_dialog.top)
            ErrorDialog(
                self.controller,
                title="Invalid Zoom Range",
                label="Error: Invalid x limits: " + self.left_zoom_entry_x.get() + ", " + self.right_zoom_entry_x.get(),
            )

    def apply_y(self):
        self.controller.view_notebook.select(self.tab.top)
        try:
            y1 = float(self.left_zoom_entry_y.get())
            y2 = float(self.right_zoom_entry_y.get())
            self.tab.adjust_y(y1, y2)
            utils.lift_widget(self.plot_settings_dialog.top)
        except ValueError:
            utils.lift_widget(self.plot_settings_dialog.top)
            ErrorDialog(
                self.controller,
                title="Invalid Zoom Range",
                label="Error! Invalid y limits: " + self.left_zoom_entry_y.get() + ", " + self.right_zoom_entry_y.get(),
            )

    def apply_z(self):
        self.controller.view_notebook.select(self.tab.top)

        try:
            z1 = float(self.left_zoom_entry_z.get())
            z2 = float(self.right_zoom_entry_z.get())
            self.tab.adjust_z(z1, z2)
            utils.lift_widget(self.plot_settings_dialog.top)
        except ValueError:  # TODO: Make sure invalid range can't cause other errors.
            utils.lift_widget(self.plot_settings_dialog.top)
            ErrorDialog(
                self.controller,
                title="Invalid Zoom Range",
                label="Error: Invalid z limits: " + self.left_zoom_entry_z.get() + ", " + self.right_zoom_entry_z.get(),
            )

    def set_title(self):
        self.tab.set_title(self.title_entry.get())
        utils.lift_widget(self.plot_settings_dialog.top)

    def set_custom_color(self, custom_color):
        self.tab.set_color(self.color_sample_var.get(), custom_color)
        utils.lift_widget(self.plot_settings_dialog.top)

    def set_color(self):
        if self.color_color_var.get() == "Custom":
            custom_color = None
            try:
                self.custom_color_dialog.top.destroy()
            except AttributeError:
                pass
            self.custom_color_dialog = CustomColorDialog(self.controller, self.set_custom_color, custom_color)
            utils.lift_widget(self.custom_color_dialog.top)
        else:
            self.tab.set_color(self.color_sample_var.get(), self.color_color_var.get())

        utils.lift_widget(self.plot_settings_dialog.top)

    def set_linestyle(self):
        self.tab.set_linestyle(self.linestyle_sample_var.get(), self.linestyle_linestyle_var.get())
        utils.lift_widget(self.plot_settings_dialog.top)

    def set_markerstyle(self):
        self.tab.set_markerstyle(self.markerstyle_sample_var.get(), self.markerstyle_markerstyle_var.get())
        utils.lift_widget(self.plot_settings_dialog.top)

    def set_legend(self):
        self.tab.set_legend_style(self.legend_legend_var.get())
        utils.lift_widget(self.plot_settings_dialog.top)
