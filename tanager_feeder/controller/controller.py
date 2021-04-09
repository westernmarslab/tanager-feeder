import os
import time
from threading import Thread
from typing import Dict, List, Any, Optional


# pylint: disable = not-callable
# Get quite a number of false (I think) not callable errors.
# pylint: disable = method-hidden
# Dummy ControllerType used for type hinting leads to lots of pylint method-hidden warnings.

import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter import (
    Button,
    Frame,
    Entry,
    Event,
    RIGHT,
    LEFT,
    Tk,
    Label,
    BOTH,
    Menu,
    NORMAL,
    DISABLED,
    ttk,
    StringVar,
    IntVar,
    Radiobutton,
    OptionMenu,
    INSERT,
    TclError,
)

import numpy as np

from tanager_feeder.controller.cli_manager import CliManager
from tanager_feeder.controller.console import Console
from tanager_feeder.controller.analysis_tools_manager import AnalysisToolsManager
from tanager_feeder.controller.edit_plot_manager import EditPlotManager
from tanager_feeder.controller.failsafes_manager import FailsafesManager
from tanager_feeder.controller.plot_manager import PlotManager
from tanager_feeder.controller.plot_settings_manager import PlotSettingsManager
from tanager_feeder.controller.process_manager import ProcessManager, ProcessFileError

from tanager_feeder.command_handlers.config_handler import ConfigHandler
from tanager_feeder.command_handlers.data_handler import DataHandler
from tanager_feeder.command_handlers.get_position_handler import GetPositionHandler
from tanager_feeder.command_handlers.instrument_config_handler import InstrumentConfigHandler
from tanager_feeder.command_handlers.motion_handler import MotionHandler
from tanager_feeder.command_handlers.opt_handler import OptHandler
from tanager_feeder.command_handlers.process_handler import ProcessHandler
from tanager_feeder.command_handlers.save_config_handler import SaveConfigHandler
from tanager_feeder.command_handlers.spectrum_handler import SpectrumHandler
from tanager_feeder.command_handlers.white_reference_handler import WhiteReferenceHandler
from tanager_feeder.command_handlers.restart_rs3_handler import RestartRS3Handler
from tanager_feeder.command_handlers.restart_computer_handler import RestartComputerHandler
from tanager_feeder.command_handlers.check_writeable_handler import CheckWriteableHandler
from tanager_feeder.command_handlers.list_contents_handler import ListContentsHandler

from tanager_feeder.commanders.spec_commander import SpecCommander
from tanager_feeder.commanders.pi_commander import PiCommander

from tanager_feeder.dialogs.remote_file_explorer import RemoteFileExplorer
from tanager_feeder.dialogs.config_dialog import ConfigDialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.dialog import Dialog

from tanager_feeder.goniometer_view.goniometer_view import GoniometerView

from tanager_feeder.listeners.pi_listener import PiListener
from tanager_feeder.listeners.spec_listener import SpecListener

from tanager_feeder.plotter.plotter import Plotter
from tanager_feeder.remote_directory_worker import RemoteDirectoryWorker
from tanager_feeder.utils import VerticalScrolledFrame, MovementUnits, sin, cos, arctan
from tanager_feeder import utils


class Controller(utils.ControllerType):
    def __init__(self, connection_manager: utils.ConnectionManager, config_info: utils.ConfigInfo):
        self.connection_manager = connection_manager
        self.config_info = config_info
        self.tk_format = utils.TkFormat(self.config_info)

        # The queue is a list of dictionaries commands:parameters
        # The commands are supposed to be executed in order, assuming each one succeeds.
        # CommandHandlers tell the controller when it's time to do the next one
        self.queue = []

        self.restarting_spec_compy = False
        self.white_referencing = False
        self.white_reference_attempt = 0
        self.opt_attempt = 0
        self.overwrite_all = False  # User can say yes to all for overwriting files.

        self.tk_buttons = []
        self.entries = []
        self.radiobuttons = []
        self.tk_check_buttons = []
        self.option_menus = []

        try:
            self.spec_listener = SpecListener(connection_manager, config_info)
        except OSError as e:
            if e.args[0] != 10048:
                raise
            dialog = Dialog(
                None,
                "Error: Multiple connections",
                "Only one usage of the Tanager Feeder socket address is permitted."
                "\nClose other programs and try again."
                "\n\nIf the issue persists, restart your computer.",
                buttons={"ok": {utils.exit_func: []}},
            )
            dialog.top.wm_geometry("300x200")
        self.spec_listener.set_controller(self)
        self.spec_listener.start()

        try:
            self.pi_listener = PiListener(connection_manager, config_info)
        except OSError as e:
            if e.args[0] != 10048:
                raise
            Dialog(
                None,
                "Error: Multiple connections",
                "Only one usage of the Tanager Feeder socket address is permitted."
                "\nClose other programs and try again.",
                buttons={"ok": {utils.exit_func: []}},
            )

        self.pi_listener.set_controller(self)
        self.pi_listener.start()

        self.spec_commander = SpecCommander(self.connection_manager, self.spec_listener)
        self.pi_commander = PiCommander(self.connection_manager, self.pi_listener)

        self.remote_directory_worker = RemoteDirectoryWorker(self.spec_commander, self.spec_listener)



        # One wait dialog open at a time. CommandHandlers check whether to use an existing one or make a new one.
        self.wait_dialog = None

        self.min_science_i = -70
        self.max_science_i = 70
        self.min_motor_i = -90
        self.max_motor_i = 90
        self.science_i = None
        self.final_i = None
        self.i_interval = None

        self.min_science_e = -70
        self.max_science_e = 70
        self.min_motor_e = -90
        self.max_motor_e = 90
        self.science_e = None  # current emission angle
        self.final_e = None
        self.e_interval = None

        self.min_science_az = 0
        self.max_science_az = 179
        self.min_motor_az = -179
        self.max_motor_az = 270
        self.science_az = None  # current azimuth angle
        self.final_az = None
        self.az_interval = None

        self.required_angular_separation = 10
        self.required_angular_separation_for_fiber = 10

        # cmds the user has entered into the console. Allows scrolling back
        # and forth through commands by using up and down arrows.

        self.script_failed = False
        self.script_running = False
        self.text_only = False  # for running scripts.
        self.frozen = False



        self.audio_signals = False

        # These will get set via user input.
        self.spec_save_path = ""
        self.spec_basename = ""
        self.spec_num = None
        self.spec_config_count = None
        self.take_spectrum_with_bad_i_or_e = False

        self.current_label = ""

        self.incidence_entries = []
        self.incidence_labels = []
        self.emission_entries = []
        self.emission_labels = []
        self.azimuth_entries = []
        self.azimuth_labels = []

        self.active_incidence_entries = []  # list of geometries where data is currently being collected
        self.active_emission_entries = []
        self.active_azimuth_entries = []

        self.geometry_frames = []
        self.active_geometry_frames = []
        self.geometry_removal_buttons = []  # buttons for removing geometries from GUI

        self.sample_removal_buttons = []  # As each sample is added, it also gets an associated button for removing it.

        self.sample_label_entries = []  # Entries for holding sample names
        self.sample_labels = []  # Labels next to those entries
        self.pos_menus = []  # Option menus for each sample telling which position to put it in
        self.sample_pos_vars = []  # Variables associated with each menu telling its current value
        self.sample_frames = []  # Frames holding all of these things.
        # New one gets created each time a sample is added to the GUI.

        self.sample_tray_index = None  # The location of the physical sample tray. This will be an integer -1 to 4
        # corresponding to wr (-1) or an index in the available_sample_positions (0-4). This is a confusing system
        # (sorry).
        self.current_sample_gui_index = 0  # This might be different from the tray position. For example, if samples
        # are set in trays 2 and 4 only then the gui_index will range from 0 (wr) to 1 (tray 2).
        self.available_sample_positions = [
            "Sample 1",
            "Sample 2",
            "Sample 3",
            "Sample 4",
            "Sample 5",
        ]  # All available positions. Does not change.
        self.taken_sample_positions = []  # Filled positions. Changes as samples are added and removed.
        self.add_sample_button = None
        self.add_geometry_button = None

        self.master = Tk()
        self.master.configure(background=self.tk_format.bg)

        self.master.title("Control")
        self.master.minsize(1050, 400)
        # When the window closes, send a command to set the geometry to i=0, e=30.
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.menubar = Menu(self.master)
        # create a pulldown menu, and add it to the menu bar
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load script", command=self.load_script)
        self.filemenu.add_command(label="Process and export data", command=self.show_process_frame)
        self.filemenu.add_command(label="Plot processed data", command=self.show_plot_frame)
        self.filemenu.add_command(label="Clear plotted data cache", command=self.reset_plot_data)

        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)

        self.menubar.add_cascade(label="File", menu=self.filemenu)

        # create more pulldown menus
        editmenu = Menu(self.menubar, tearoff=0)
        editmenu.add_command(label="Failsafes...", command=self.show_settings_frame)
        #         editmenu.add_command(label="Plot settings...", command=self.show_plot_settings_frame)
        self.audiomenu = Menu(editmenu, tearoff=0)
        self.audiomenu.add_command(label="  Enabled", command=self.enable_audio)
        self.audiomenu.add_command(label="X Disabled", command=self.disable_audio)
        editmenu.add_cascade(label="Audio signals", menu=self.audiomenu)

        self.goniometermenu = Menu(editmenu, tearoff=0)
        self.goniometermenu.add_command(label="X Manual", command=lambda: self.set_manual_automatic(force=0))
        self.goniometermenu.add_command(label="  Automatic", command=lambda: self.set_manual_automatic(force=1))
        editmenu.add_cascade(label="Goniometer control", menu=self.goniometermenu)

        self.geommenu = Menu(editmenu, tearoff=0)
        self.geommenu.add_command(label="X Individual", command=lambda: self.set_individual_range(0))
        self.geommenu.add_command(
            label="  Range (Automatic only)", command=lambda: self.set_individual_range(1), state=DISABLED
        )
        editmenu.add_cascade(label="Geometry specification", menu=self.geommenu)
        editmenu.add_command(label="Goniometer config...", command=self.show_config_dialog)

        self.menubar.add_cascade(label="Settings", menu=editmenu)

        helpmenu = Menu(self.menubar, tearoff=0)
        # helpmenu.add_command(label="About", command=hello)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

        # display the menu
        self.master.config(menu=self.menubar)

        self.notebook_frame = Frame(self.master)
        self.notebook_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.notebook = ttk.Notebook(self.notebook_frame)


        self.view_frame = Frame(self.master, width=1800, height=1200, bg=self.tk_format.bg)
        self.view_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        self.view_notebook_holder = Frame(self.view_frame, width=1800, height=1200)
        self.view_notebook_holder.pack(fill=BOTH, expand=True)
        self.view_notebook = ttk.Notebook(self.view_notebook_holder)
        self.view_notebook.pack()

        self.goniometer_view = GoniometerView(self, self.view_notebook)
        self.view_notebook.bind("<<NotebookTabChanged>>", lambda event: self.goniometer_view.tab_switch(event))

        # The plotter manages all the plots.
        self.plotter = Plotter(
            self,
            self.get_dpi(),
            [
                self.config_info.global_config_loc + "color_config.mplstyle",
                self.config_info.global_config_loc + "size_config.mplstyle",
            ],
        )

        self.process_manager = ProcessManager(self)
        self.failsafes_manager = FailsafesManager(self)
        self.edit_plot_manager = EditPlotManager(self)
        self.process_manager = ProcessManager(self)
        self.plot_manager = PlotManager(self)
        self.plot_settings_manager = PlotSettingsManager(self)
        self.analysis_tools_manager = AnalysisToolsManager(self)
        self.cli_manager = CliManager(self)

        try:
            with open(self.config_info.local_config_loc + "spec_save.txt", "r") as spec_save_config:
                self.spec_save_path = spec_save_config.readline().strip("\n")
                self.spec_basename = spec_save_config.readline().strip("\n")
                self.spec_startnum = str(int(spec_save_config.readline().strip("\n")) + 1)
                while len(self.spec_startnum) < self.config_info.num_len:
                    self.spec_startnum = "0" + self.spec_startnum
        except OSError:
            with open(self.config_info.local_config_loc + "spec_save.txt", "w+") as f:
                f.write("C:\\Users\n")
                f.write("basename\n")
                f.write("-1\n")

                self.spec_save_path = "C:\\Users"
                self.spec_basename = "basename"
                self.spec_startnum = "0"
                while len(self.spec_startnum) < self.config_info.num_len:
                    self.spec_startnum = "0" + self.spec_startnum

        try:
            with open(self.config_info.local_config_loc + "script_config.txt", "r") as script_config:
                self.script_loc = script_config.readline().strip("\n")
        except OSError:
            with open(self.config_info.local_config_loc + "script_config.txt", "w+") as script_config:
                script_config.write(os.getcwd())
                self.script_loc = os.getcwd()
        self.notebook_frames = []

        self.control_frame = VerticalScrolledFrame(self, self.notebook_frame, bg=self.tk_format.bg)
        self.control_frame.pack(fill=BOTH, expand=True)

        self.save_config_frame = Frame(self.control_frame.interior, bg=self.tk_format.bg, highlightthickness=1)
        self.save_config_frame.pack(fill=BOTH, expand=True)
        self.spec_save_label = Label(
            self.save_config_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Raw spectral data save configuration:",
        )
        self.spec_save_label.pack(pady=(15, 5))
        self.spec_save_path_label = Label(
            self.save_config_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Directory:",
        )
        self.spec_save_path_label.pack(padx=self.tk_format.padx)

        self.spec_save_dir_frame = Frame(self.save_config_frame, bg=self.tk_format.bg)
        self.spec_save_dir_frame.pack()

        self.spec_save_dir_browse_button = Button(
            self.spec_save_dir_frame, text="Browse", command=self.choose_spec_save_dir
        )
        self.tk_buttons.append(self.spec_save_dir_browse_button)
        self.spec_save_dir_browse_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        self.spec_save_dir_browse_button.pack(side=RIGHT, padx=(3, 15), pady=(5, 10))

        self.spec_save_dir_var = StringVar()
        self.spec_save_dir_var.trace("w", self.validate_spec_save_dir)
        self.spec_save_dir_entry = Entry(
            self.spec_save_dir_frame,
            width=50,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
            textvariable=self.spec_save_dir_var,
        )
        self.entries.append(self.spec_save_dir_entry)
        self.spec_save_dir_entry.insert(0, self.spec_save_path)
        self.spec_save_dir_entry.pack(padx=(15, 5), pady=(5, 10), side=RIGHT)
        self.spec_save_frame = Frame(self.save_config_frame, bg=self.tk_format.bg)
        self.spec_save_frame.pack()

        self.spec_basename_label = Label(
            self.spec_save_frame,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Base name:",
        )
        self.spec_basename_label.pack(side=LEFT, pady=self.tk_format.pady)

        self.spec_basename_var = StringVar()
        self.spec_basename_var.trace("w", self.validate_basename)
        self.spec_basename_entry = Entry(
            self.spec_save_frame,
            width=10,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
            textvariable=self.spec_basename_var,
        )
        self.entries.append(self.spec_basename_entry)
        self.spec_basename_entry.pack(side=LEFT, padx=(5, 5), pady=self.tk_format.pady)
        self.spec_basename_entry.insert(0, self.spec_basename)

        self.spec_startnum_label = Label(
            self.spec_save_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Number:",
        )
        self.spec_startnum_label.pack(side=LEFT, pady=self.tk_format.pady)

        self.startnum_var = StringVar()
        self.startnum_var.trace("w", self.validate_startnum)
        self.spec_startnum_entry = Entry(
            self.spec_save_frame,
            width=10,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
            textvariable=self.startnum_var,
        )
        self.entries.append(self.spec_startnum_entry)
        self.spec_startnum_entry.insert(0, self.spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=self.tk_format.pady)

        self.instrument_config_frame = Frame(self.control_frame.interior, bg=self.tk_format.bg, highlightthickness=1)
        self.spec_settings_label = Label(
            self.instrument_config_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Instrument Configuration:",
        )
        self.spec_settings_label.pack(padx=self.tk_format.padx, pady=(10, 10))
        self.instrument_config_frame.pack(fill=BOTH, expand=True)
        self.i_config_label_entry_frame = Frame(self.instrument_config_frame, bg=self.tk_format.bg)
        self.i_config_label_entry_frame.pack()
        self.instrument_config_label = Label(
            self.i_config_label_entry_frame,
            fg=self.tk_format.textcolor,
            text="Number of spectra to average:",
            bg=self.tk_format.bg,
        )
        self.instrument_config_label.pack(side=LEFT, padx=(20, 0))

        self.instrument_config_entry = Entry(
            self.i_config_label_entry_frame,
            width=10,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.instrument_config_entry)
        self.instrument_config_entry.insert(0, 200)
        self.instrument_config_entry.pack(side=LEFT)

        self.viewing_geom_options_frame = Frame(self.control_frame.interior, bg=self.tk_format.bg)

        self.viewing_geom_options_frame_left = Frame(
            self.viewing_geom_options_frame, bg=self.tk_format.bg, highlightthickness=1
        )
        self.viewing_geom_options_frame_left.pack(side=LEFT, fill=BOTH, expand=True)

        self.single_mult_frame = Frame(self.viewing_geom_options_frame, bg=self.tk_format.bg, highlightthickness=1)
        self.single_mult_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        self.angle_control_label = Label(
            self.single_mult_frame,
            text="Geometry specification:      ",
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
        )
        self.angle_control_label.pack(padx=(5, 5), pady=(10, 5))

        self.individual_range = IntVar()
        self.individual_radio = Radiobutton(
            self.single_mult_frame,
            text="Individual         ",
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            highlightthickness=0,
            variable=self.individual_range,
            value=0,
            selectcolor=self.tk_format.check_bg,
            command=self.set_individual_range,
        )
        self.radiobuttons.append(self.individual_radio)
        self.individual_radio.pack()

        self.range_radio = Radiobutton(
            self.single_mult_frame,
            text="Range with interval\n(Automatic only)",
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            highlightthickness=0,
            variable=self.individual_range,
            value=1,
            selectcolor=self.tk_format.check_bg,
            command=self.set_individual_range,
        )
        self.radiobuttons.append(self.range_radio)
        self.range_radio.configure(state=DISABLED)
        self.range_radio.pack()

        self.gon_control_label_frame = Frame(self.viewing_geom_options_frame_left, bg=self.tk_format.bg)
        self.gon_control_label_frame.pack()
        self.gon_control_label = Label(
            self.gon_control_label_frame,
            text="\nGoniometer control:         ",
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
        )
        self.gon_control_label.pack(side=LEFT, padx=(10, 5))

        self.manual_radio_frame = Frame(self.viewing_geom_options_frame_left, bg=self.tk_format.bg)
        self.manual_radio_frame.pack()
        self.manual_automatic = IntVar()
        self.manual_radio = Radiobutton(
            self.manual_radio_frame,
            text="Manual            ",
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            highlightthickness=0,
            variable=self.manual_automatic,
            value=0,
            selectcolor=self.tk_format.check_bg,
            command=self.set_manual_automatic,
        )
        self.radiobuttons.append(self.manual_radio)
        self.manual_radio.pack(side=LEFT, padx=(10, 10), pady=(5, 5))

        self.automation_radio_frame = Frame(self.viewing_geom_options_frame_left, bg=self.tk_format.bg)
        self.automation_radio_frame.pack()
        self.automation_radio = Radiobutton(
            self.automation_radio_frame,
            text="Automatic         ",
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            highlightthickness=0,
            variable=self.manual_automatic,
            value=1,
            selectcolor=self.tk_format.check_bg,
            command=self.set_manual_automatic,
        )
        self.radiobuttons.append(self.automation_radio)
        self.automation_radio.pack(side=LEFT, padx=(10, 10))
        self.filler_label = Label(self.viewing_geom_options_frame_left, text="", bg=self.tk_format.bg)
        self.filler_label.pack()

        self.viewing_geom_frame = Frame(self.control_frame.interior, bg=self.tk_format.bg, highlightthickness=1)
        self.viewing_geom_frame.pack(fill=BOTH, expand=True)

        self.viewing_geom_options_label = Label(
            self.viewing_geom_frame, text="Viewing geometry:", fg=self.tk_format.textcolor, bg=self.tk_format.bg
        )
        self.viewing_geom_options_label.pack(pady=(10, 10))

        self.individual_angles_frame = Frame(
            self.viewing_geom_frame, bg=self.tk_format.bg, highlightbackground=self.tk_format.border_color
        )
        self.individual_angles_frame.pack()
        self.add_geometry()

        self.range_frame = Frame(
            self.viewing_geom_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bd=2,
            highlightbackground=self.tk_format.border_color,
            highlightcolor=self.tk_format.border_color,
            highlightthickness=0,
            bg=self.tk_format.bg,
        )
        # self.range_frame.pack()
        self.light_frame = Frame(self.range_frame, bg=self.tk_format.bg)
        self.light_frame.pack(side=LEFT, padx=(5, 5))
        self.light_label = Label(
            self.light_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Incidence angles:",
        )
        self.light_label.pack()

        light_labels_frame = Frame(
            self.light_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        light_labels_frame.pack(side=LEFT)

        light_start_label = Label(
            light_labels_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="First:",
        )
        light_start_label.pack(pady=(0, 8), padx=(40, 0))
        light_end_label = Label(
            light_labels_frame,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            fg=self.tk_format.textcolor,
            text="Last:",
        )
        light_end_label.pack(pady=(0, 5), padx=(40, 0))
        light_increment_label = Label(
            light_labels_frame,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            fg=self.tk_format.textcolor,
            text="Increment:",
        )
        light_increment_label.pack(pady=(0, 5), padx=(0, 0))

        light_entries_frame = Frame(
            self.light_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        light_entries_frame.pack(side=RIGHT)

        self.light_start_entry = Entry(
            light_entries_frame,
            width=5,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.light_start_entry)
        self.light_start_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)
        self.light_end_entry = Entry(
            light_entries_frame,
            width=5,
            highlightbackground="white",
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.light_end_entry)
        self.light_end_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)
        self.light_increment_entry = Entry(
            light_entries_frame,
            width=5,
            highlightbackground="white",
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.light_increment_entry)
        self.light_increment_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)

        detector_frame = Frame(self.range_frame, bg=self.tk_format.bg)
        detector_frame.pack(side=LEFT)

        detector_label = Label(
            detector_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Emission angles:",
        )
        detector_label.pack()

        detector_labels_frame = Frame(
            detector_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        detector_labels_frame.pack(side=LEFT, padx=(5, 5))

        detector_start_label = Label(
            detector_labels_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="First:",
        )
        detector_start_label.pack(pady=(0, 8), padx=(40, 0))
        detector_end_label = Label(
            detector_labels_frame,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            fg=self.tk_format.textcolor,
            text="Last:",
        )
        detector_end_label.pack(pady=(0, 5), padx=(40, 0))

        detector_increment_label = Label(
            detector_labels_frame,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            fg=self.tk_format.textcolor,
            text="Increment:",
        )
        detector_increment_label.pack(pady=(0, 5), padx=(0, 0))

        detector_entries_frame = Frame(
            detector_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        detector_entries_frame.pack(side=RIGHT)
        self.detector_start_entry = Entry(
            detector_entries_frame,
            bd=self.tk_format.bd,
            width=5,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.detector_start_entry)
        self.detector_start_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)

        self.detector_end_entry = Entry(
            detector_entries_frame,
            bd=self.tk_format.bd,
            width=5,
            highlightbackground="white",
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.detector_end_entry)
        self.detector_end_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)

        self.detector_increment_entry = Entry(
            detector_entries_frame,
            bd=self.tk_format.bd,
            width=5,
            highlightbackground="white",
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.detector_increment_entry)
        self.detector_increment_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)

        self.azimuth_frame = Frame(self.range_frame, bg=self.tk_format.bg)
        self.azimuth_frame.pack(side=LEFT, padx=(5, 5))
        self.azimuth_label = Label(
            self.azimuth_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Azimuth angles:",
        )
        self.azimuth_label.pack()

        azimuth_labels_frame = Frame(
            self.azimuth_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        azimuth_labels_frame.pack(side=LEFT)

        azimuth_start_label = Label(
            azimuth_labels_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="First:",
        )
        azimuth_start_label.pack(pady=(0, 8), padx=(40, 0))
        azimuth_end_label = Label(
            azimuth_labels_frame,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            fg=self.tk_format.textcolor,
            text="Last:",
        )
        azimuth_end_label.pack(pady=(0, 5), padx=(40, 0))

        azimuth_increment_label = Label(
            azimuth_labels_frame,
            bg=self.tk_format.bg,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            fg=self.tk_format.textcolor,
            text="Increment:",
        )
        azimuth_increment_label.pack(pady=(0, 5), padx=(0, 0))

        azimuth_entries_frame = Frame(
            self.azimuth_frame, bg=self.tk_format.bg, padx=self.tk_format.padx, pady=self.tk_format.pady
        )
        azimuth_entries_frame.pack(side=RIGHT)

        self.azimuth_start_entry = Entry(
            azimuth_entries_frame,
            width=5,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.azimuth_start_entry)
        self.azimuth_start_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)

        self.azimuth_end_entry = Entry(
            azimuth_entries_frame,
            width=5,
            highlightbackground="white",
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.azimuth_end_entry)
        self.azimuth_end_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)
        self.azimuth_increment_entry = Entry(
            azimuth_entries_frame,
            width=5,
            highlightbackground="white",
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.entries.append(self.azimuth_increment_entry)
        self.azimuth_increment_entry.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)

        self.samples_frame = Frame(self.control_frame.interior, bg=self.tk_format.bg, highlightthickness=1)
        self.samples_frame.pack(fill=BOTH, expand=True)

        self.samples_label = Label(
            self.samples_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.bg,
            fg=self.tk_format.textcolor,
            text="Samples:",
        )
        self.samples_label.pack(pady=(10, 10))

        self.add_sample()

        self.gen_frame = Frame(self.control_frame.interior, bg=self.tk_format.bg, highlightthickness=1, pady=10)
        self.gen_frame.pack(fill=BOTH, expand=True)

        self.action_button_frame = Frame(self.gen_frame, bg=self.tk_format.bg)
        self.action_button_frame.pack()

        self.opt_button = Button(
            self.action_button_frame,
            fg=self.tk_format.textcolor,
            text="Optimize",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=self.tk_format.button_width,
            bg="light gray",
            command=self.opt_button_cmd,
            height=2,
        )
        self.tk_buttons.append(self.opt_button)
        self.opt_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        self.opt_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady, side=LEFT)
        self.wr_button = Button(
            self.action_button_frame,
            fg=self.tk_format.textcolor,
            text="White Reference",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=self.tk_format.button_width,
            bg="light gray",
            command=self.wr_button_cmd,
            height=2,
        )
        self.tk_buttons.append(self.wr_button)
        self.wr_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady, side=LEFT)
        self.wr_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )

        self.spec_button = Button(
            self.action_button_frame,
            fg=self.tk_format.textcolor,
            text="Take Spectrum",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=self.tk_format.button_width,
            height=2,
            bg="light gray",
            command=self.spec_button_cmd,
        )
        self.tk_buttons.append(self.spec_button)
        self.spec_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady, side=LEFT)
        self.spec_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )

        self.acquire_button = Button(
            self.action_button_frame,
            fg=self.tk_format.textcolor,
            text="Acquire Data",
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            width=self.tk_format.button_width,
            height=2,
            bg="light gray",
            command=self.acquire,
        )
        self.tk_buttons.append(self.acquire_button)
        self.acquire_button.config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )

        self.console = Console(self)

        if not self.connection_manager.pi_offline:
            self.set_manual_automatic(force=1)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        thread = Thread(target=self.bind)
        thread.start()

        thread = Thread(
            target=self.scrollbar_check
        )  # Waits for everything to get packed, then checks if you need a scrollbar on the control frame.
        thread.start()
        if self.config_info.opsys == "Windows":
            self.master.wm_state("zoomed")
        self.master.mainloop()

    @property
    def science_i(self):
        return self.__science_i

    @science_i.setter
    def science_i(self, value):
        if value is None:
            self.__science_i = value
        else:
            try:
                self.__science_i = int(value)
            except ValueError:
                raise Exception("Invalid science i value") from ValueError

    @property
    def science_e(self):
        return self.__science_e

    @science_e.setter
    def science_e(self, value):
        if value is None:
            self.__science_e = value
        else:
            try:
                self.__science_e = int(value)
            except ValueError:
                raise Exception("Invalid science e value") from ValueError

    @property
    def science_az(self):
        return self.__science_az

    @science_az.setter
    def science_az(self, value):
        if value is None:
            self.__science_az = value
        else:
            try:
                self.__science_az = int(value)
            except ValueError:
                raise Exception("Invalid science az value") from ValueError

    def scrollbar_check(self) -> None:
        time.sleep(0.5)
        self.control_frame.update()

    # called when user goes to File > Process and export data
    def show_process_frame(self) -> None:
        self.process_manager.show()

    def enable_audio(self) -> None:
        self.audio_signals = True
        self.audiomenu.entryconfigure(0, label="X Enabled")
        self.audiomenu.entryconfigure(1, label="  Disabled")

    def disable_audio(self) -> None:
        self.audio_signals = False
        self.audiomenu.entryconfigure(0, label="  Enabled")
        self.audiomenu.entryconfigure(1, label="X Disabled")

    # Show failsafes settings frame
    def show_settings_frame(self) -> None:
        self.failsafes_manager.show()

    def show_plot_frame(self) -> None:
        self.plot_manager.show()

    def plot_remote(self, filename: str) -> None:
        self.queue.insert(0, {self.plot_remote: [filename]})
        plot_loc = os.path.join(self.config_info.local_config_loc, "plot_temp.csv")
        self.queue.insert(1, {self.plot_manager.plot: [plot_loc]})
        self.spec_commander.transfer_data(filename)
        DataHandler(
            self,
            destination=plot_loc,
        )

    def bind(self) -> None:
        # This is probably important but I don't remember exactly how it works. Somethign to do with setting up the GUI.
        self.master.bind("<Configure>", self.resize)
        time.sleep(0.2)
        window = utils.PretendEvent(self.master, self.master.winfo_width(), self.master.winfo_height())
        self.resize(window)
        time.sleep(0.2)
        if not self.connection_manager.spec_offline:
            self.log("Spec compy connected.")
        else:
            self.log("Spec compy not connected. Working offline. Restart to collect spectral data.")
        if not self.connection_manager.pi_offline:
            self.log("Raspberry pi connected.")
        else:
            self.log("Raspberry pi not connected. Working offline. Restart to use automation features.")

    def on_closing(self) -> None:
        self.master.destroy()
        utils.exit_func()

    def load_script(self) -> None:
        self.script_running = True
        self.script_failed = False

        script_file = askopenfilename(initialdir=self.script_loc, title="Select script")
        if script_file == "":
            self.script_running = False
            self.queue = []
            return
        self.queue = []

        with open(self.config_info.local_config_loc + "script_config.txt", "w") as script_config:
            if self.config_info.opsys == "Linux" or self.config_info.opsys == "Mac":
                self.script_loc = "/".join(script_file.split("/")[0:-1])
            else:
                self.script_loc = "\\".join(script_file.split("\\")[0:-1])
            script_config.write(self.script_loc)

        with open(script_file, "r") as script:
            cmd = script.readline().strip("\n")
            while cmd != "":
                self.queue.append({self.next_script_line: [cmd]})
                cmd = script.readline().strip("\n")
                continue
        self.queue.append({self.next_script_line: ["end file"]})
        self.next_in_queue()

    def next_script_line(self, cmd: str) -> None:
        self.script_running = True
        if cmd == "end file":
            self.log("Script complete")
            self.script_running = False
            self.queue = []
        if self.script_failed:
            self.log("Exiting")
            self.queue = []
        else:
            self.unfreeze()
            self.console.console_entry.delete(0, "end")
            self.console.console_entry.insert(0, cmd)
            self.freeze()
            self.execute_cmd()

    # use this to make plots - matplotlib works in inches but we want to use pixels.
    def get_dpi(self) -> None:
        MM_TO_IN = 1 / 25.4
        pxw = self.master.winfo_screenwidth()
        inw = self.master.winfo_screenmmwidth() * MM_TO_IN
        return pxw / inw

    # when operating in manual mode, check validity of viewing geom when the user clicks buttons. If valid, update
    # graphic and self.i and self.e before moving on to other checks. Return any warnings.
    def check_viewing_geom_for_manual_operation(self) -> str:
        warnings = ""

        valid_i = utils.validate_int_input(self.incidence_entries[0].get(), -90, 90)
        print(valid_i)
        if valid_i:
            if str(self.science_i) != self.incidence_entries[0].get():
                self.failsafes_manager.angles_change_time = time.time()
            self.science_i = int(self.incidence_entries[0].get())

        else:
            warnings += "The incidence angle is invalid (Min:" + str(-90) + ", Max:" + str(90) + ").\n\n"

        valid_e = utils.validate_int_input(self.emission_entries[0].get(), -90, 90)
        if valid_e:
            if str(self.science_e) != self.emission_entries[0].get():
                self.failsafes_manager.angles_change_time = time.time()
            self.science_e = int(self.emission_entries[0].get())
        else:
            warnings += "The emission angle is invalid (Min:" + str(-90) + ", Max:" + str(90) + ").\n\n"

        valid_az = utils.validate_int_input(self.azimuth_entries[0].get(), 0, 179)
        if valid_az:
            if str(self.science_az) != self.azimuth_entries[0].get():
                self.failsafes_manager.angles_change_time = time.time()
            self.science_az = int(self.azimuth_entries[0].get())
        else:
            warnings += "The azimuth angle is invalid (Min:" + str(0) + ", Max:" + str(179) + ").\n\n"

        if valid_i and valid_e and valid_az:
            i = int(self.incidence_entries[0].get())
            e = int(self.emission_entries[0].get())
            az = int(self.azimuth_entries[0].get())
            valid_separation = self.validate_distance(i, e, az)

            if valid_e and valid_i and valid_az and not valid_separation:
                warnings += (
                    "Light source and detector should be at least "
                    + str(self.required_angular_separation)
                    + " degrees apart.\n\n"
                )
        #             self.set_and_animate_geom()

        return warnings

    # Check whether the current save configuration for raw spectral is different from the last one saved. If it is,
    # send commands to the spec compy telling it so.
    def check_save_config(self) -> str:
        new_spec_save_dir = self.spec_save_dir_entry.get()
        new_spec_basename = self.spec_basename_entry.get()
        try:
            new_spec_num = int(self.spec_startnum_entry.get())
        except ValueError:
            return "invalid"

        if new_spec_save_dir == "" or new_spec_basename == "" or new_spec_num == "":
            return "invalid"

        if (
            new_spec_save_dir != self.spec_save_path
            or new_spec_basename != self.spec_basename
            or self.spec_num is None
            or new_spec_num != self.spec_num
        ):
            return "not_set"
        return "set"

    def check_mandatory_input(self) -> bool:
        save_config_status = self.check_save_config()
        if save_config_status == "invalid":
            ErrorDialog(self, label="Error: Please enter a valid save configuration.")
            return False

        try:
            new_spec_config_count = int(self.instrument_config_entry.get())
            if new_spec_config_count < 1 or new_spec_config_count > 32767:
                raise ValueError
        except ValueError:
            ErrorDialog(self, label="Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767")
            return False

        if self.manual_automatic.get() == 1:  # 0 is manual, 1 is automatic
            for index in range(len(self.active_incidence_entries)):
                i = self.active_incidence_entries[index].get()
                e = self.active_emission_entries[index].get()
                az = self.active_azimuth_entries[index].get()
                valid_i = utils.validate_int_input(i, self.min_science_i, self.max_science_i)
                valid_e = utils.validate_int_input(e, self.min_science_e, self.max_science_e)
                valid_az = utils.validate_int_input(az, self.min_science_az, self.max_science_az)
                if not valid_i or not valid_e or not valid_az:
                    ErrorDialog(
                        self,
                        label="Error: Invalid viewing geometry:\n\nincidence = "
                        + str(i)
                        + "\nemission = "
                        + str(e)
                        + "\nazimuth = "
                        + str(az),
                        width=300,
                        height=130,
                    )
                    return False
                i, e, az = int(i), int(e), int(az)
                if not self.validate_distance(i, e, az):
                    ErrorDialog(
                        self,
                        label="Error: Due to geometric constraints on the goniometer,\nincidence must be at least "
                        + str(self.required_angular_separation)
                        + " degrees different than emission.",
                        width=300,
                        height=130,
                    )
                    return False

        return True

    # Setup gets called after we already know that input is valid, but before we've set up the specrometer control
    # software. If we need to set RS3's save configuration or the instrument configuration (number of spectra to
    # average), it puts those things into the queue saying we will need to do them when we start.
    def setup_RS3_config(self, nextaction: Any) -> bool:
        if self.manual_automatic.get() == 0:
            thread = Thread(target=self.set_and_animate_geom)
            thread.start()

        # Requested save config is guaranteed to be valid because of input checks above.
        save_config_status = self.check_save_config()
        if save_config_status == "not_set":
            self.complete_queue_item()
            self.queue.insert(0, nextaction)
            self.queue.insert(0, {self.set_save_config: []})
            self.set_save_config()
            return False

        # Requested instrument config is guaranteed to be valid because of input checks above.
        new_spec_config_count = int(self.instrument_config_entry.get())
        if self.spec_config_count is None or str(new_spec_config_count) != str(self.spec_config_count):
            self.complete_queue_item()
            self.queue.insert(0, nextaction)
            self.queue.insert(0, {self.configure_instrument: []})
            self.configure_instrument()
            return False

        file = open(self.config_info.local_config_loc + "spec_save.txt", "w")
        file.write(self.spec_save_dir_entry.get() + "\n")
        file.write(self.spec_basename_entry.get() + "\n")
        file.write(self.spec_startnum_entry.get() + "\n")
        self.process_manager.process_input_dir = self.spec_save_dir_entry.get()
        return True

    # acquire is called every time opt, wr, or take spectrum buttons are pushed from manual mode
    # also called if acquire button is pushed in automatic mode
    # Action will be either wr, take_spectrum, or opt (manual mode) OR it might just be 'acquire' (automatic mode)
    # For any of these things, we need to validate input.
    def acquire(self, override: bool = False, setup_complete: bool = False, action: Any = None, garbage: bool = False):
        if not self.frozen:
            self.freeze()
        # pylint: disable = comparison-with-callable
        if not setup_complete:
            # Make sure basenum entry has the right number of digits. It is already guaranteed to have no more digits
            # than allowed and to only have numbers.
            start_num = self.spec_startnum_entry.get()
            num_zeros = self.config_info.num_len - len(start_num)
            for _ in range(num_zeros):
                start_num = "0" + start_num
            utils.set_text(self.spec_startnum_entry, start_num)

            # Set all entries to active. Viewing geometry information will be pulled from these one at a time. Entries
            # are removed from the active list after the geom info is read.
            self.active_incidence_entries = list(self.incidence_entries)
            self.active_emission_entries = list(self.emission_entries)
            self.active_azimuth_entries = list(self.azimuth_entries)
            self.active_geometry_frames = list(self.geometry_frames)

        range_warnings = ""
        if (
            action is None
        ):  # If this was called by the user clicking acquire. otherwise, it will be take_spectrum or wr?
            action = self.acquire
            self.queue.insert(0, {self.acquire: []})
            if self.individual_range.get() == 1:
                valid_range = self.range_setup()
                if not valid_range:
                    return
                if isinstance(valid_range, str):
                    # If there was a warning associated with the input check for the range setup e.g. interval
                    # specified as zero, then we'll log this as a warning for the user coming up.
                    range_warnings = valid_range

        if not override:
            # If input isn't valid and the user asks to continue, take_spectrum will be called again with override set
            # to True
            ok = (
                self.check_mandatory_input()
            )  # check things that have to be right in order to continue e.g. valid number of spectra to average
            if not ok:
                return

            # now check things that are optional e.g. having reasonable sample labels, taking a white reference at
            # every geom.
            valid_input = False
            if action == self.take_spectrum:
                valid_input = self.failsafes_manager.check_optional_input(
                    self.take_spectrum, [True, False, garbage], range_warnings
                )
            elif action in (self.acquire, self.wr):
                valid_input = self.failsafes_manager.check_optional_input(action, [True, False], range_warnings)
            elif action == self.opt:
                valid_input = self.failsafes_manager.check_optional_input(self.opt, [True, False], range_warnings)
            if not valid_input:
                return
                # Make sure RS3 save config and instrument config are taken care of. This will add those actions to the
                # queue if needed.

        if not setup_complete:
            if action == self.take_spectrum:
                setup = self.setup_RS3_config({self.take_spectrum: [True, False, garbage]})
            elif action in (self.wr, self.acquire):
                setup = self.setup_RS3_config({action: [True, False]})
            elif action == self.opt:
                setup = self.setup_RS3_config(
                    {self.opt: [True, False]}
                )  # override=True (because we just checked those things?), setup_complete=False

            else:
                raise Exception("Error: Unknown action")
            # If things were not already set up (instrument config, etc) then the compy will take care of that and call
            # take_spectrum again after it's done.
            if not setup:
                return

        if action == self.take_spectrum:
            startnum_str = str(self.spec_startnum_entry.get())
            while len(startnum_str) < self.config_info.num_len:
                startnum_str = "0" + startnum_str
            if not garbage:
                if self.white_referencing:
                    # This will be true when we are saving the spectrum after the white reference
                    label = "White Reference"
                else:
                    label = self.sample_label_entries[self.current_sample_gui_index].get()
                self.spec_commander.take_spectrum(
                    self.spec_save_path,
                    self.spec_basename,
                    startnum_str,
                    label,
                    self.science_i,
                    self.science_e,
                    self.science_az,
                )
                SpectrumHandler(self)
            else:
                self.spec_commander.take_spectrum(
                    self.spec_save_path,
                    self.spec_basename,
                    startnum_str,
                    "GARBAGE",
                    self.science_i,
                    self.science_e,
                    self.science_az,
                )
                SpectrumHandler(self, title="Collecting garbage...", label="Collecting garbage spectrum...")

        elif action == self.wr:
            self.spec_commander.white_reference()
            WhiteReferenceHandler(self)

        elif action == self.opt:
            self.spec_commander.optimize()
            OptHandler(self)

        elif action == self.acquire:
            self.build_queue()
            self.next_in_queue()

    def build_queue(self) -> None:
        script_queue = list(
            self.queue
        )  # If we're running a script, the queue might have a lot of commands in it that will need to be executed
        # after we're done acquiring. save these, we'll append them in a moment.
        self.queue = []

        # For each (i, e, az), opt, white reference, save the white reference, move the tray, take a  spectrum, then
        # move the tray back, then update geom to next.
        next_emission = self.science_e  # Define this here so as not to get an
        # error if len(self.active_emission_entries) == 0 (not sure if this is a real case).

        for index, entry in enumerate(self.active_emission_entries):
            # This is one for each geometry when geometries are specified individually. When a range is specified,
            # we actually quietly create pretend entry objects for each pair, so it works then too.
            if index == 0:
                # Params to next geom:
                # For the first, don't complete anything.
                # Do keep the emission arm above -50 to avoid danger of running oversized samples into the arm.
                # For emission angles < -50, complete the movement later. Don't have to worry about it
                # for first movement if if we're already at wr position
                if self.sample_tray_index > -1:
                    self.queue.append({self.next_geom: [False, True]})
                else:
                    self.queue.append({self.next_geom: [False, False]})
            else:
                self.queue.append({self.next_geom: [True, True]})

            next_emission = int(entry.get())
            self.queue.append({self.move_tray: ["wr"]})
            if next_emission < -50 or next_emission > 50:
                self.queue.append({self.set_emission: [next_emission, MovementUnits.ANGLE.value]})
            self.queue.append({self.opt: [True, True]})
            self.queue.append({self.wr: [True, True]})
            self.queue.append({self.take_spectrum: [True, True, False]})
            for pos in self.taken_sample_positions:  # e.g. 'Sample 1'
                if next_emission < -50:
                    self.queue.append({self.set_emission: [-50, MovementUnits.ANGLE.value]})
                    self.queue.append({self.move_tray: [pos]})
                    self.queue.append({self.set_emission: [next_emission, MovementUnits.ANGLE.value]})
                elif next_emission > 50:
                    self.queue.append({self.set_emission: [50, MovementUnits.ANGLE.value]})
                    self.queue.append({self.move_tray: [pos]})
                    self.queue.append({self.set_emission: [next_emission, MovementUnits.ANGLE.value]})
                else:
                    self.queue.append({self.move_tray: [pos]})
                self.queue.append({self.take_spectrum: [True, True, True]})  # Save and delete a garbage spectrum
                self.queue.append({self.take_spectrum: [True, True, False]})  # Save a real spectrum

        # Return tray to wr position when finished
        if next_emission < -50:
            self.queue.append({self.set_emission: [-50, MovementUnits.ANGLE.value]})
        if next_emission > 50:
            self.queue.append({self.set_emission: [50, MovementUnits.ANGLE.value]})
        self.queue.append({self.move_tray: ["wr"]})

        # Now append the script queue we saved at the beginning. But check if acquire is the first command in the
        # script queue and if it is, complete that item.
        if self.script_running:
            if len(script_queue) > 0:
                while self.acquire in script_queue[0]:
                    script_queue.pop(0)
            self.queue = self.queue + script_queue

    # updates motor and science angle values, animates goniometer arms moving
    def set_and_animate_geom(self, complete_queue_item: bool = False) -> None:
        if self.manual_automatic.get() == 1:  # automatic mode
            next_science_i = int(self.active_incidence_entries[0].get())
            next_science_e = int(self.active_emission_entries[0].get())
            next_science_az = int(self.active_azimuth_entries[0].get())

        else:  # in manual mode, it's ok if the specified geometry is invalid.
            try:
                next_science_i = int(self.incidence_entries[0].get())
            except ValueError:
                next_science_i = None

            try:
                next_science_e = int(self.emission_entries[0].get())
            except ValueError:
                next_science_e = None

            try:
                next_science_az = int(self.azimuth_entries[0].get())
            except ValueError:
                next_science_az = None

        if self.science_i != next_science_i or self.science_e != next_science_e or self.science_az != next_science_az:
            self.failsafes_manager.angles_change_time = time.time()

        self.science_i = next_science_i
        self.science_e = next_science_e
        self.science_az = next_science_az

        valid_i = utils.validate_int_input(next_science_i, self.min_science_i, self.max_science_i)
        valid_e = utils.validate_int_input(next_science_e, self.min_science_e, self.max_science_e)
        valid_az = utils.validate_int_input(next_science_az, self.min_science_az, self.max_science_az)

        temp_queue = []
        if not (valid_i and valid_e and valid_az):
            if self.manual_automatic.get() == 1:
                raise Exception(
                    "Invalid geometry: " + str(next_science_i) + " " + str(next_science_e) + " " + str(next_science_az)
                )
            if valid_i:
                self.goniometer_view.set_incidence(next_science_i)
            if valid_e:
                self.goniometer_view.set_emission(next_science_e)
            if valid_az:
                self.goniometer_view.set_azimuth(next_science_az)

        else:
            movements = self.get_movements(next_science_i, next_science_e, next_science_az)

            for movement in movements:
                if "az" in movement:
                    next_motor_az = movement["az"]
                    temp_queue.append({self.goniometer_view.set_azimuth: [next_motor_az]})
                elif "e" in movement:
                    next_motor_e = movement["e"]
                    temp_queue.append({self.goniometer_view.set_emission: [next_motor_e]})
                elif "i" in movement:
                    next_motor_i = movement["i"]
                    temp_queue.append({self.goniometer_view.set_incidence: [next_motor_i]})

        if complete_queue_item:
            if len(self.queue) > 0:
                self.complete_queue_item()

            self.queue = temp_queue + self.queue
            if len(self.queue) > 0:
                self.next_in_queue()
        else:
            for dictionary in temp_queue:
                for func in dictionary:
                    args = dictionary[func]
                    func(*args)

    def get_movements(self, next_science_i: int, next_science_e: int, next_science_az: int) -> List[Dict]:
        current_i, current_az = self.science_i, self.science_az
        # This is the case if we're just calling set_display
        if current_i is None:
            current_i = self.goniometer_view.position["science_i"]
        if current_az is None:
            current_az = self.goniometer_view.position["science_az"]

        movement_order = [{"i": next_science_i}, {"e": next_science_e}, {"az": next_science_az}]
        if next_science_i < -60:
            # pylint: disable = chained-comparison
            if (current_az <= 65 and next_science_az > 65) or (
                current_az >= 115 and next_science_az < 115
            ):  # passing through/into danger zone
                movement_order = [{"i": -60}, {"e": next_science_e}, {"az": next_science_az}, {"i": next_science_i}]
                print("Moving through or into danger!")
            elif 65 < current_az < 115 and current_i < -65:  # Already in danger zone
                print("Starting in danger!")
                if next_science_az != current_az:
                    movement_order = [{"i": -60}, {"e": next_science_e}, {"az": next_science_az}, {"i": next_science_i}]
        return movement_order

    def next_geom(self, complete_last: bool = True, cap_at_minus_50=False) -> None:
        self.complete_queue_item()
        if complete_last:
            self.active_incidence_entries.pop(0)
            self.active_emission_entries.pop(0)
            self.active_azimuth_entries.pop(0)
            if self.individual_range.get() == 0:
                self.active_geometry_frames.pop(0)

        next_i = int(self.active_incidence_entries[0].get())
        next_e = int(self.active_emission_entries[0].get())
        if cap_at_minus_50:  # This is to prevent accidentally running oversized samples into the fiber optic.
            if next_e < -50:
                next_e = -50
            elif next_e > 50:
                next_e = 50
        next_az = int(self.active_azimuth_entries[0].get())

        # Update goniometer position. Don't run the arms into each other
        movements = self.get_movements(next_i, next_e, next_az)
        temp_queue = []
        for movement in movements:
            if "az" in movement:
                next_motor_az = movement["az"]
                temp_queue.append({self.set_azimuth: [next_motor_az]})
            elif "e" in movement:
                next_motor_e = movement["e"]
                temp_queue.append({self.set_emission: [next_motor_e]})
            elif "i" in movement:
                next_motor_i = movement["i"]
                temp_queue.append({self.set_incidence: [next_motor_i]})

        self.queue = temp_queue + self.queue
        self.next_in_queue()

    # Move light will either read i from the GUI (default, i=None), or if this is a text command then i will be passed
    # as a parameter. When from the commandline, i may not be an incidence angle at all but a number of steps to move.
    # In this case, type will be 'steps'.
    def set_incidence(self, next_i: Optional[int] = None, unit: str = MovementUnits.ANGLE.value) -> None:
        if unit == "angle":
            # First check whether we actually need to move at all.
            if next_i is None:
                next_i = int(self.active_incidence_entries[0].get())

            if next_i == self.science_i:  # No change in incidence angle, no need to move
                self.log("Goniometer remaining at an incidence angle of " + str(self.science_i) + " degrees.")
                self.complete_queue_item()
                if len(self.queue) > 0:
                    self.next_in_queue()
                return  # If we're staying in the same spot, just return!
            timeout = np.abs(next_i - self.science_i) + utils.PI_BUFFER
        else:
            timeout = np.abs(next_i) / 15 + utils.PI_BUFFER

        self.pi_commander.set_incidence(next_i, unit)
        MotionHandler(
            self,
            label="Setting incidence...",
            timeout=timeout,
            steps=(unit == MovementUnits.STEPS.value),
            destination=next_i,
        )

        if unit == MovementUnits.ANGLE.value:  # Only change the visualization if an angle is specified.
            self.goniometer_view.set_incidence(next_i)

    def set_emission(self, next_e: Optional[int] = None, unit: str = MovementUnits.ANGLE.value) -> None:
        if unit == "angle":
            # First check whether we actually need to move at all.
            if next_e is None:
                next_e = int(self.active_emission_entries[0].get())

            if next_e == self.science_e:  # No change in emission angle, no need to move
                self.log("Goniometer remaining at an emission angle of " + str(self.science_e) + " degrees.")
                self.complete_queue_item()
                if len(self.queue) > 0:
                    self.next_in_queue()
                return  # If we're staying in the same spot, just return!
            timeout = np.abs(next_e - self.science_e) + utils.PI_BUFFER
        else:
            timeout = np.abs(next_e) / 15 + utils.PI_BUFFER

        self.pi_commander.set_emission(next_e, unit)
        MotionHandler(
            self,
            label="Setting emission...",
            timeout=timeout,
            steps=(unit == MovementUnits.STEPS.value),
            destination=next_e,
        )

        if unit == MovementUnits.ANGLE.value:  # Only change the visualization if an angle is specified.
            self.goniometer_view.set_emission(next_e)

    def set_azimuth(self, next_az: Optional[int] = None, unit: str = MovementUnits.ANGLE.value) -> None:
        if unit == "angle":
            # First check whether we actually need to move at all.
            if next_az is None:
                next_az = int(self.active_azimuth_entries[0].get())

            if next_az == self.science_az:  # No change in azimuth angle, no need to move
                self.log("Goniometer remaining at an azimuth angle of " + str(self.science_az) + " degrees.")
                self.complete_queue_item()
                if len(self.queue) > 0:
                    self.next_in_queue()
                return  # If we're staying in the same spot, just return!
            timeout = np.abs(next_az - self.science_az) + utils.PI_BUFFER
        else:
            timeout = np.abs(next_az) / 15 + utils.PI_BUFFER

        self.pi_commander.set_azimuth(next_az, unit)
        MotionHandler(
            self,
            label="Setting azimuth...",
            timeout=timeout,
            steps=(unit == MovementUnits.STEPS.value),
            destination=next_az,
        )

        if unit == MovementUnits.ANGLE.value:  # Only change the visualization if an angle is specified.
            self.goniometer_view.set_azimuth(next_az)

    def move_tray(self, pos: str, unit=MovementUnits.POSITION.value) -> None:
        if unit == "position":
            self.goniometer_view.set_current_sample(pos)
        self.pi_commander.move_tray(pos, unit)
        MotionHandler(
            self,
            label="Moving sample tray...",
            timeout=30 + utils.BUFFER,
            new_sample_loc=pos,
            steps=(unit == MovementUnits.STEPS.value),
        )

    def range_setup(self) -> None:
        self.active_incidence_entries = []
        self.active_emission_entries = []
        self.active_azimuth_entries = []

        incidence_err_str = ""
        incidence_warn_str = ""

        first_i = self.light_start_entry.get()
        valid = utils.validate_int_input(first_i, self.min_science_i, self.max_science_i)
        if not valid:
            incidence_err_str = (
                "Incidence must be a number from " + str(self.min_science_i) + " to " + str(self.max_science_i) + ".\n"
            )
        else:
            first_i = int(first_i)

        final_i = self.light_end_entry.get()
        valid = utils.validate_int_input(final_i, self.min_science_i, self.max_science_i)

        if not valid:
            incidence_err_str = (
                "Incidence must be a number from " + str(self.min_science_i) + " to " + str(self.max_science_i) + ".\n"
            )
        else:
            final_i = int(final_i)

        i_interval = self.light_increment_entry.get()
        valid = utils.validate_int_input(i_interval, 0, 2 * self.max_science_i)
        if not valid:
            incidence_err_str += "Incidence interval must be a number from 0 to " + str(2 * self.max_science_i) + ".\n"
        else:
            i_interval = int(i_interval)
        incidences = []
        if incidence_err_str == "":
            if i_interval == 0:
                if first_i == final_i:
                    incidences = [first_i]
                else:
                    incidences = [first_i, final_i]
                    incidence_warn_str = "Incidence interval = 0. Using first and last given incidence values.\n"
            elif final_i > first_i:
                incidences = np.arange(first_i, final_i, i_interval)
                incidences = list(incidences)
                incidences.append(final_i)
            else:
                incidences = np.arange(first_i, final_i, -1 * i_interval)
                incidences = list(incidences)
                incidences.append(final_i)

        emission_err_str = ""
        emission_warn_str = ""

        first_e = self.detector_start_entry.get()
        valid = utils.validate_int_input(first_e, self.min_science_e, self.max_science_e)
        if not valid:
            emission_err_str = (
                "Emission must be a number from " + str(self.min_science_e) + " to " + str(self.max_science_e) + ".\n"
            )
        else:
            first_e = int(first_e)
        final_e = self.detector_end_entry.get()
        valid = utils.validate_int_input(final_e, self.min_science_e, self.max_science_e)

        if not valid:
            emission_err_str = (
                "Emission must be a number from " + str(self.min_science_e) + " to " + str(self.max_science_e) + ".\n"
            )
        else:
            final_e = int(final_e)

        e_interval = self.detector_increment_entry.get()
        valid = utils.validate_int_input(e_interval, 0, 2 * self.max_science_e)
        if not valid:
            emission_err_str += "Emission interval must be a number from 0 to " + str(2 * self.max_science_e) + ".\n"
        else:
            e_interval = int(e_interval)
        emissions = []
        if emission_err_str == "":
            if e_interval == 0:
                if first_e == final_e:
                    emissions = [first_e]
                else:
                    emissions = [first_e, final_e]
                    emission_warn_str = "Emission interval = 0. Using first and last given emission values."
            elif final_e > first_e:
                emissions = np.arange(first_e, final_e, e_interval)
                emissions = list(emissions)
                emissions.append(final_e)
            else:
                emissions = np.arange(first_e, final_e, -1 * e_interval)
                emissions = list(emissions)
                emissions.append(final_e)

        err_str = "Error: " + incidence_err_str + emission_err_str
        if err_str != "Error: ":
            ErrorDialog(self, title="Error", label=err_str)
            return False

        azimuth_err_str = ""
        azimuth_warn_str = ""

        first_az = self.azimuth_start_entry.get()
        valid = utils.validate_int_input(first_az, self.min_science_az, self.max_science_az)
        if not valid:
            azimuth_err_str = (
                "Azimuth must be a number from " + str(self.min_science_az) + " to " + str(self.max_science_az) + ".\n"
            )
        else:
            first_az = int(first_az)
        final_az = self.azimuth_end_entry.get()
        valid = utils.validate_int_input(final_az, self.min_science_az, self.max_science_az)

        if not valid:
            azimuth_err_str = (
                "Azimuth must be a number from " + str(self.min_science_az) + " to " + str(self.max_science_az) + ".\n"
            )
        else:
            final_az = int(final_az)

        az_interval = self.azimuth_increment_entry.get()
        valid = utils.validate_int_input(az_interval, 0, 2 * self.max_science_az)
        if not valid:
            azimuth_err_str += "Azimuth interval must be a number from 0 to " + str(2 * self.max_science_az) + ".\n"
        else:
            az_interval = int(az_interval)
        azimuths = []
        if azimuth_err_str == "":
            if az_interval == 0:
                if first_az == final_az:
                    azimuths = [first_az]
                else:
                    azimuths = [first_az, final_az]
                    azimuth_warn_str = "Azimuth interval = 0. Using first and last given azimuth values."
            elif final_az > first_az:
                azimuths = np.arange(first_az, final_az, az_interval)
                azimuths = list(azimuths)
                azimuths.append(final_az)
            else:
                azimuths = np.arange(first_az, final_az, -1 * az_interval)
                azimuths = list(azimuths)
                azimuths.append(final_az)

        for i in incidences:
            for e in emissions:
                for az in azimuths:
                    if self.include_in_auto_range(i, e, az):
                        i_entry = utils.PrivateEntry(str(i))
                        e_entry = utils.PrivateEntry(str(e))
                        az_entry = utils.PrivateEntry(str(az))
                        self.active_incidence_entries.append(i_entry)
                        self.active_emission_entries.append(e_entry)
                        self.active_azimuth_entries.append(az_entry)

        warning_string = incidence_warn_str + emission_warn_str + azimuth_warn_str
        if warning_string == "":
            return True
        return warning_string

    def include_in_auto_range(self, i: int, e: int, az: int) -> bool:
        if not self.check_if_good_measurement(i, e, az):
            return False  # Don't include because the measurement won't work because the light will be shining
            # on/through the emission arm.
        if i < -60 and 65 < az < 115:
            return False  # Don't include because the clearance between the emission motor and the light source
            # is too tight for comfort
        return True  # Otherwise it's good!

    # References: https://www.movable-type.co.uk/scripts/latlong.html
    #            https://en.wikipedia.org/wiki/Great-circle_navigation
    #            http://astrophysicsformulas.com/astronomy-formulas-astrophysics-
    #            formulas/angular-distance-between-two-points-on-a-sphere
    def check_if_good_measurement(self, i: int, e: int, az: int) -> bool:
        # check if the measurement will be ruined by the emission arm being in the way of the light source.
        # start by checking if the light will be incident on the collimator
        if not self.validate_distance(i, e, az):
            return False
        if i >= 10:  # If incidence is positive, light won't hit the detector arm.
            return True
        # Next check if the light will hit the detector arm
        if not self.check_light_misses_arc(i, e, az, self.required_angular_separation):
            return False
        # And finally check if the light will hit the fiber optic cable, which has az = az -35
        if not self.check_light_misses_arc(i, e, az + 25, self.required_angular_separation_for_fiber):
            return False
        return True

    @staticmethod
    def check_light_misses_arc(i, e, az, required_sep, print_me=False):
        # This is the azimuthal distance between the arc the light source travels
        # and the detector arm. -90 to 90 because i is negative.
        arm_bottom_az = az - 90
        bearing = utils.get_initial_bearing(e)
        closest_dist = utils.get_phase_angle(i, e, az)
        points = np.arange(0, 90, 3)
        points = np.append(points, 90)
        arm_lat = []
        arm_delta_long = []

        for point in points:
            tan_lat = cos(bearing) * sin(point) / np.sqrt(cos(point) ** 2 + sin(bearing) ** 2 * sin(point) ** 2)
            lat = arctan(tan_lat)
            arm_lat.append(lat)
            tan_long = sin(bearing) * sin(point) / cos(point)
            long = arctan(tan_long)
            arm_delta_long.append(long)
        arm_delta_long = np.array(arm_delta_long)
        if e <= 0:
            arm_azes = arm_bottom_az + arm_delta_long
        else:
            arm_azes = arm_bottom_az - arm_delta_long

        for num, lat in enumerate(arm_lat):
            arm_e = 90 - lat
            dist = utils.get_phase_angle(i, -1 * arm_e, arm_azes[num])
            if dist < closest_dist:
                closest_dist = dist
        if print_me:
            print(closest_dist)
        if closest_dist >= required_sep:
            return True
        return False

    # called when user clicks optimize button. No different than opt() except we clear out the queue first just in case
    # there is something leftover hanging out in there.
    def opt_button_cmd(self) -> None:
        self.queue = []
        self.queue.append(
            {self.opt: [True, True]}
        )  # Setting override and setup_complete to True make is so if we automatically retry because of an error on
        # the spec compy we won't have to do setup things agian.
        self.acquire(override=False, setup_complete=False, action=self.opt)

    # called when user clicks wr button. No different than wr() except we freeze buttons and clear out the queue first
    # just in case there is something leftover hanging out in there.
    def wr_button_cmd(self) -> None:
        self.queue = []
        self.queue.append(
            {self.wr: [True, True]}
        )  # Setting override and setup_complete to True make is so if we automatically retry because of an error on
        # the spec compy we won't have to do setup things agian.
        self.queue.append({self.take_spectrum: [True, True, False]})
        self.acquire(override=False, setup_complete=False, action=self.wr)

    # called when user clicks take spectrum button. No different than take_spectrum() except we clear out the queue
    # first just in case there is something leftover hanging out in there.
    def spec_button_cmd(self) -> None:
        self.queue = []
        self.queue.append(
            {self.take_spectrum: [False, False, False]}
        )  # We don't automatically retry taking spectra so there is no need to have override and setup complete set to
        # true here as for the other two above.
        self.acquire(override=False, setup_complete=False, action=self.take_spectrum, garbage=False)

    # commands that are put in the queue for optimizing, wr, taking a spectrum.
    def opt(self, override: bool = False, setup_complete: bool = False) -> None:
        self.acquire(override=override, setup_complete=setup_complete, action=self.opt)

    def wr(self, override: bool = False, setup_complete: bool = False) -> None:
        self.acquire(override=override, setup_complete=setup_complete, action=self.wr)

    def take_spectrum(self, override: bool, setup_complete: bool, garbage: bool) -> None:
        self.acquire(override=override, setup_complete=setup_complete, action=self.take_spectrum, garbage=garbage)

    def restart_computer(self):
        self.spec_commander.restart_computer()
        self.connection_manager.spec_offline = True
        RestartComputerHandler(self)

    def restart_rs3(self):
        self.spec_commander.restart_rs3()
        RestartRS3Handler(self)

    def configure_instrument(self) -> None:
        self.spec_commander.configure_instrument(self.instrument_config_entry.get())
        InstrumentConfigHandler(self)

    def check_writeable(self):
        self.spec_commander.check_writeable(self.spec_save_dir_entry.get())
        CheckWriteableHandler(self)

    def list_contents(self):
        status = self.remote_directory_worker.get_dirs(self.spec_save_dir_entry.get())
        ListContentsHandler(self, status)

    # Set thes ave configuration for raw spectral data. First, use a remotedirectoryworker to check whether the
    # directory exists and is writeable. If it doesn't exist, give an option to create the directory.
    def set_save_config(self) -> None:
        self.queue.insert(1, {self.set_save_config_part_2: []})
        self.list_contents()

    def set_save_config_part_2(self):
        self.queue.insert(1, {self.finish_set_save_config: []})
        self.check_writeable()

    def finish_set_save_config(self):
        spec_num = self.spec_startnum_entry.get()
        while len(spec_num) < self.config_info.num_len:
            spec_num = "0" + spec_num

        self.spec_commander.set_save_path(
            self.spec_save_dir_entry.get(), self.spec_basename_entry.get(), self.spec_startnum_entry.get()
        )
        SaveConfigHandler(self)

    def reset(self) -> None:
        self.clear_queue()
        self.overwrite_all = False
        self.script_running = False
        self.script_failed = False
        self.white_referencing = False

    # execute a command either input into the console by the user or loaded from a script
    def execute_cmd(self, event: Optional[Event] = None) -> None:
        # pylint: disable = unused-argument
        if self.script_running:
            self.complete_queue_item()

        # self.text_only = True
        command = self.console.next_cmd()
        thread = Thread(target=self.cli_manager.execute_cmd, kwargs={"cmd": command})
        thread.start()

    def fail_script_command(self, message: str) -> None:
        self.log(message)
        self.queue = []
        self.script_running = False
        if self.wait_dialog is not None:
            try:
                self.wait_dialog.interrupt(message)
                self.wait_dialog.top.wm_geometry("376x140")
            except TclError:
                pass

    def increment_num(self) -> None:
        try:
            num = int(self.spec_startnum_entry.get()) + 1
            self.spec_startnum_entry.delete(0, "end")
            self.spec_startnum_entry.insert(0, str(num))
        except ValueError:
            return

    def process_cmd(
        self,
        input_directory: Optional[str] = None,
        output_directory: Optional[str] = None,
        output_file: Optional[str] = None,
    ) -> None:
        if input_directory is None or output_directory is None or output_file is None:
            try:
                input_directory, output_directory, output_file = self.process_manager.setup_process()
            except ProcessFileError:
                print("Process File Error!")
                return
        if self.process_manager.proc_local.get() == 1:
            self.spec_commander.process(input_directory, "spec_temp_data_loc", output_file)
            self.queue.insert(0, {self.process_cmd: [input_directory, output_directory, output_file]})
            self.queue.insert(
                1,
                {
                    self.finish_process: [
                        os.path.join("spec_temp_data_loc", output_file),
                        os.path.join(output_directory, output_file),
                    ]
                },
            )
        else:
            self.spec_commander.process(input_directory, output_directory, output_file)
            self.queue.insert(0, {self.process_cmd: [input_directory, output_directory, output_file]})
        try:
            self.process_manager.process_top.destroy()
        except TclError:
            print("Error: Could not close process window.")
            pass
        ProcessHandler(self, os.path.join(output_directory, output_file))

    def finish_process(self, source_file, output_file) -> None:
        print("Finishing process")
        print(self.queue)
        return
        self.spec_commander.transfer_data(source_file)
        DataHandler(
            self,
            destination=output_file,
        )
        return

    # This gets called when the user clicks 'Edit plot' from the right-click menu on a plot.
    # Pops up a scrollable listbox with sample options.
    def ask_plot_samples(self, tab, existing_sample_indices, sample_options, existing_geoms, current_title):
        self.close_plot_option_windows()
        self.edit_plot_manager.show(tab, existing_sample_indices, sample_options, existing_geoms, current_title)

    def open_analysis_tools(self, tab):
        self.close_plot_option_windows()
        if len(tab.existing_indices) == 0:
            ErrorDialog(self, "Error: Nothing plotted.", "Error: Nothing plotted.")
            return
        self.analysis_tools_manager.show(tab)

    def open_plot_settings(self, tab):
        self.close_plot_option_windows()
        if tab.x_axis == "contour":
            self.plot_settings_manager.show(tab)
        elif len(tab.existing_indices) == 0:
            ErrorDialog(self, "Error: Nothing plotted.", "Error: Nothing plotted.")
            return
        else:
            self.plot_settings_manager.show(tab)

    # If the user already has analysis tools or a plot editing dialog open, close the extra to avoid confusion.
    def close_plot_option_windows(self):
        try:
            self.analysis_tools_manager.analysis_dialog.top.destroy()
        except (AttributeError, TclError):
            pass
        try:
            self.edit_plot_manager.edit_plot_dialog.top.destroy()
        except (AttributeError, TclError):
            pass
        try:
            self.plot_settings_manager.plot_settings_dialog.top.destroy()
        except (AttributeError, TclError):
            pass
        try:
            self.plot_manager.plot_top.destroy()
        except (AttributeError, TclError):
            pass

    def reset_plot_data(self):
        self.plotter = Plotter(
            self,
            self.get_dpi(),
            [
                self.config_info.global_config_loc + "color_config.mplstyle",
                self.config_info.global_config_loc + "size_config.mplstyle",
            ],
        )
        for i, tab in enumerate(self.view_notebook.tabs()):
            if i == 0:
                continue
            self.view_notebook.forget(tab)
        self.plot_manager = PlotManager(self)

    def choose_spec_save_dir(self):
        RemoteFileExplorer(
            self,
            label="Select a directory to save raw spectral data.\nThis must be to a drive mounted on the spectrometer"
            " control computer.\n E.g. R:\\RiceData\\MarsGroup\\YourName\\spectral_data",
            target=self.spec_save_dir_entry,
        )

    def add_sample(self):
        try:
            self.add_sample_button.pack_forget()
        except (AttributeError, TclError):
            self.add_sample_button = Button(
                self.samples_frame,
                text="Add new",
                command=self.add_sample,
                width=10,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
            self.tk_buttons.append(self.add_sample_button)
            self.add_sample_button.config(
                fg=self.tk_format.buttontextcolor,
                highlightbackground=self.tk_format.highlightbackgroundcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                state=DISABLED,
            )

        self.sample_frames.append(Frame(self.samples_frame, bg=self.tk_format.bg))
        self.sample_frames[-1].pack(pady=(5, 0))

        self.control_frame.min_height += 50
        self.control_frame.update()

        self.sample_pos_vars.append(StringVar(self.master))

        self.sample_pos_vars[-1].trace("w", self.set_taken_sample_positions)
        menu_positions = []
        pos_set = False
        for pos in self.available_sample_positions:
            if pos in self.taken_sample_positions:
                pass
            elif not pos_set:
                self.sample_pos_vars[-1].set(pos)
                pos_set = True
            else:
                menu_positions.append(pos)
        if (
            len(menu_positions) == 0
        ):  # If all samples are full (i.e. this is the last sample), we need to have a value in the menu options in
            # order for it to appear on the screen. This is really a duplicate option, but Tkinter won't create an
            # OptionMenu without options.
            menu_positions.append(self.sample_pos_vars[-1].get())

        # pylint: disable = no-value-for-parameter
        self.pos_menus.append(OptionMenu(self.sample_frames[-1], self.sample_pos_vars[-1], *menu_positions))
        self.pos_menus[-1].configure(width=8, highlightbackground=self.tk_format.highlightbackgroundcolor)
        self.pos_menus[-1].pack(side=LEFT)
        self.option_menus.append(self.pos_menus[-1])

        self.sample_labels.append(
            Label(
                self.sample_frames[-1],
                bg=self.tk_format.bg,
                fg=self.tk_format.textcolor,
                text="Label:",
                padx=self.tk_format.padx,
                pady=self.tk_format.pady,
            )
        )
        self.sample_labels[-1].pack(side=LEFT, padx=(5, 0))

        self.sample_label_entries.append(
            Entry(
                self.sample_frames[-1],
                width=20,
                bd=self.tk_format.bd,
                bg=self.tk_format.entry_background,
                selectbackground=self.tk_format.selectbackground,
                selectforeground=self.tk_format.selectforeground,
            )
        )

        self.entries.append(self.sample_label_entries[-1])
        self.sample_label_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.sample_removal_buttons.append(
            Button(
                self.sample_frames[-1],
                text="Remove",
                command=lambda x=len(self.sample_removal_buttons): self.remove_sample(x),
                width=7,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
        )
        self.sample_removal_buttons[-1].config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        self.tk_buttons.append(self.sample_removal_buttons[-1])
        if len(self.sample_label_entries) > 1:
            for button in self.sample_removal_buttons:
                button.pack(side=LEFT, padx=(5, 5))

        if len(self.sample_label_entries) > len(self.available_sample_positions) - 1:
            self.add_sample_button.configure(state=DISABLED)
        self.add_sample_button.pack(pady=(10, 10))

    def remove_sample(self, index):
        self.sample_labels.pop(index)
        self.sample_label_entries.pop(index)
        self.sample_pos_vars.pop(index)
        self.sample_removal_buttons.pop(index)
        self.sample_frames.pop(index).destroy()
        self.pos_menus.pop(index)

        for i, button in enumerate(self.sample_removal_buttons):
            button.configure(command=lambda x=i: self.remove_sample(x))
        if self.manual_automatic.get() == 1:
            self.add_sample_button.configure(state=NORMAL)
        if len(self.sample_label_entries) == 1:
            self.sample_removal_buttons[0].pack_forget()

        self.set_taken_sample_positions()

        self.control_frame.min_height -= 50  # Reduce the required size for the control frame to display all elements.
        self.control_frame.update()  # Configure scrollbar.

    def set_taken_sample_positions(self, *args):
        # pylint: disable = unused-argument
        # args contains a tuple of tkinter pyvars. e.g. ('PY_VAR39', '', 'w'). Not used.
        self.taken_sample_positions = []
        for var in self.sample_pos_vars:
            self.taken_sample_positions.append(var.get())

        # Now remake all option menus with taken sample positions not listed in options unless that was the option that
        # was already selected for them.
        menu_positions = []
        for pos in self.available_sample_positions:
            if pos in self.taken_sample_positions:
                pass
            else:
                menu_positions.append(pos)

        for i, _ in enumerate(self.pos_menus):
            local_menu_positions = list(menu_positions)
            if (
                len(menu_positions) == 0
            ):  # If all samples are full, we need to have a value in the menu options in order for it to appear on the
                # screen. This is really a duplicate option, but Tkinter won't create an OptionMenu without options,
                # so having it in there prevents errors.
                local_menu_positions.append(self.sample_pos_vars[i].get())
            self.pos_menus[i]["menu"].delete(0, "end")
            # pylint: disable = protected-access
            for choice in local_menu_positions:
                self.pos_menus[i]["menu"].add_command(label=choice, command=tk._setit(self.sample_pos_vars[i], choice))

    def remove_geometry(self, index):
        self.incidence_labels.pop(index)
        self.incidence_entries.pop(index)
        self.azimuth_labels.pop(index)
        self.azimuth_entries.pop(index)
        self.emission_entries.pop(index)
        self.emission_labels.pop(index)
        self.geometry_removal_buttons.pop(index)
        self.geometry_frames.pop(index).destroy()

        for i, button in enumerate(self.geometry_removal_buttons):
            button.configure(command=lambda x=i: self.remove_geometry(x))
        if self.manual_automatic.get() == 1:
            self.add_geometry_button.configure(state=NORMAL)
        if len(self.incidence_entries) == 1:
            self.geometry_removal_buttons[0].pack_forget()

    def add_geometry(self):
        try:
            self.add_geometry_button.pack_forget()
        except (AttributeError, TclError):
            self.add_geometry_button = Button(
                self.individual_angles_frame,
                text="Add new",
                command=self.add_geometry,
                width=10,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
            self.tk_buttons.append(self.add_geometry_button)
            self.add_geometry_button.config(
                fg=self.tk_format.buttontextcolor,
                highlightbackground=self.tk_format.highlightbackgroundcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                state=DISABLED,
            )

        self.geometry_frames.append(Frame(self.individual_angles_frame, bg=self.tk_format.bg))
        self.geometry_frames[-1].pack(pady=(5, 0))

        self.incidence_labels.append(
            Label(
                self.geometry_frames[-1],
                bg=self.tk_format.bg,
                fg=self.tk_format.textcolor,
                text="i:",
                padx=self.tk_format.padx,
                pady=self.tk_format.pady,
            )
        )
        self.incidence_labels[-1].pack(side=LEFT, padx=(5, 0))
        self.incidence_entries.append(
            Entry(
                self.geometry_frames[-1],
                width=10,
                bd=self.tk_format.bd,
                bg=self.tk_format.entry_background,
                selectbackground=self.tk_format.selectbackground,
                selectforeground=self.tk_format.selectforeground,
            )
        )
        self.entries.append(self.incidence_entries[-1])
        self.incidence_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.emission_labels.append(
            Label(
                self.geometry_frames[-1],
                padx=self.tk_format.padx,
                pady=self.tk_format.pady,
                bg=self.tk_format.bg,
                fg=self.tk_format.textcolor,
                text="e:",
            )
        )
        self.emission_labels[-1].pack(side=LEFT)
        self.emission_entries.append(
            Entry(
                self.geometry_frames[-1],
                width=10,
                bd=self.tk_format.bd,
                bg=self.tk_format.entry_background,
                selectbackground=self.tk_format.selectbackground,
                selectforeground=self.tk_format.selectforeground,
            )
        )
        self.entries.append(self.emission_entries[-1])
        self.emission_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.azimuth_labels.append(
            Label(
                self.geometry_frames[-1],
                bg=self.tk_format.bg,
                fg=self.tk_format.textcolor,
                text="az:",
                padx=self.tk_format.padx,
                pady=self.tk_format.pady,
            )
        )
        self.azimuth_labels[-1].pack(side=LEFT, padx=(5, 0))
        self.azimuth_entries.append(
            Entry(
                self.geometry_frames[-1],
                width=10,
                bd=self.tk_format.bd,
                bg=self.tk_format.entry_background,
                selectbackground=self.tk_format.selectbackground,
                selectforeground=self.tk_format.selectforeground,
            )
        )
        self.entries.append(self.azimuth_entries[-1])
        self.azimuth_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.geometry_removal_buttons.append(
            Button(
                self.geometry_frames[-1],
                text="Remove",
                command=lambda x=len(self.geometry_removal_buttons): self.remove_geometry(x),
                width=7,
                fg=self.tk_format.buttontextcolor,
                bg=self.tk_format.buttonbackgroundcolor,
                bd=self.tk_format.bd,
            )
        )
        self.geometry_removal_buttons[-1].config(
            fg=self.tk_format.buttontextcolor,
            highlightbackground=self.tk_format.highlightbackgroundcolor,
            bg=self.tk_format.buttonbackgroundcolor,
        )
        if len(self.incidence_entries) > 1:
            for button in self.geometry_removal_buttons:
                button.pack(side=LEFT)

        if len(self.incidence_entries) > 10:
            self.add_geometry_button.configure(state=DISABLED)
        self.add_geometry_button.pack(pady=(15, 10))

    def configure_pi(self, i: Optional[float] = None, e: Optional[float] = None, pos: Optional[int] = None):
        if i is None:
            i = self.science_i
        if e is None:
            e = self.science_e
        if pos is None:
            pos = self.sample_tray_index
        self.pi_commander.configure(i, e, pos)
        ConfigHandler(self)

    def show_config_dialog(self):
        self.freeze()
        self.queue.insert(0, {self.configure_pi: []})
        buttons = {
            "ok": {
                self.next_in_queue: [],
                self.unfreeze: [],
            },
            "cancel": {
                self.unfreeze: [],
                self.clear_queue: [],
            },
        }
        ConfigDialog(
            self,
            title="Setup Required",
            label="Setup required: Unknown goniometer state.\n\nPlease enter the current incidence, emission, and tray"
            " positions and click OK. \nNote that this will trigger the azimuth table homing routine.\n\n",
            values={
                "Incidence": [self.science_i, self.min_motor_i, self.max_motor_i],
                "Emission": [self.science_e, self.min_motor_e, self.max_motor_e],
                "Tray position": [self.sample_tray_index, 0, len(self.available_sample_positions) - 1],
            },
            buttons=buttons,
        )

    def set_manual_automatic(self, force=-1, known_goniometer_state=False):
        menu = self.goniometermenu
        if force == 0:
            self.manual_automatic.set(0)
        elif force == 1:
            self.manual_automatic.set(1)

        if self.manual_automatic.get() == 0:  # or force==0:
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
            self.range_radio.configure(state=DISABLED)
            self.individual_range.set(0)

            while len(self.incidence_entries) > 1:
                self.remove_geometry(len(self.incidence_entries) - 1)
            self.add_geometry_button.configure(state=DISABLED)
            self.add_sample_button.configure(state=DISABLED)
            for pos_menu in self.pos_menus:
                pos_menu.configure(state=DISABLED)

            self.opt_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady, side=LEFT)
            self.wr_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady, side=LEFT)
            self.spec_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady, side=LEFT)

            self.acquire_button.pack_forget()
            menu.entryconfigure(0, label="X Manual")
            menu.entryconfigure(1, label="  Automatic")
            self.geommenu.entryconfigure(0, label="X Individual")
            self.geommenu.entryconfigure(1, state=DISABLED, label="  Range (Automatic only)")
        else:
            self.add_geometry_button.configure(state=NORMAL)
            self.acquire_button.pack(padx=self.tk_format.padx, pady=self.tk_format.pady)
            self.spec_button.pack_forget()
            self.opt_button.pack_forget()
            self.wr_button.pack_forget()
            self.range_radio.configure(state=NORMAL)
            self.add_sample_button.configure(state=NORMAL)
            for pos_menu in self.pos_menus:
                pos_menu.configure(state=NORMAL)

            # This is if you are setting manual_automatic from commandline and already entered i, e, sample tray
            # position.
            if known_goniometer_state:
                menu.entryconfigure(0, label="  Manual")
                menu.entryconfigure(1, label="X Automatic")
                self.geommenu.entryconfigure(1, state=NORMAL, label="  Range (Automatic only)")
            else:
                self.get_position_from_pi()

            menu.entryconfigure(0, label="  Manual")
            menu.entryconfigure(1, label="X Automatic")
            self.geommenu.entryconfigure(1, state=NORMAL, label="  Range (Automatic only)")

    def get_position_from_pi(self):
        self.queue.insert(0, {self.pi_commander.get_current_position: []})
        self.pi_commander.get_current_position()
        GetPositionHandler(self)

    def clear_queue(self):
        self.queue = []

    def set_individual_range(self, force=-1):
        if force == 0:
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
            self.geommenu.entryconfigure(0, label="X Individual")
            self.geommenu.entryconfigure(1, label="  Range (Automatic only)")
            self.individual_range.set(0)
        elif force == 1:
            self.individual_angles_frame.pack_forget()
            self.range_frame.pack()
            self.geommenu.entryconfigure(0, label="  Individual")
            self.geommenu.entryconfigure(1, label="X Range (Automatic only)")
            self.individual_range.set(1)

    def set_overwrite_all(self, val):
        self.overwrite_all = val

    # def validate_output_filename(self):
    #     pos = self.output_filename_entry.index(INSERT)
    #     filename = utils.rm_reserved_chars(self.spec_output_filename_entry.get())
    #     filename = filename.strip("/").strip("\\")
    #     self.output_filename_entry.delete(0, "end")
    #     self.output_filename_entry.insert(0, filename)
    #     self.output_filename_entry.icursor(pos)

    def validate_spec_save_dir(self, *args):
        # pylint: disable = unused-argument
        # args contains a tuple of tkinter pyvars. e.g. ('PY_VAR39', '', 'w'). Not used.
        pos = self.spec_save_dir_entry.index(INSERT)
        spec_save_dir = utils.rm_reserved_chars(self.spec_save_dir_entry.get())
        if len(spec_save_dir) < len(self.spec_save_dir_entry.get()):
            pos = pos - 1
        self.spec_save_dir_entry.delete(0, "end")
        self.spec_save_dir_entry.insert(0, spec_save_dir)
        self.spec_save_dir_entry.icursor(pos)

    def validate_basename(self, *args):
        # pylint: disable = unused-argument
        # args contains a tuple of tkinter pyvars. e.g. ('PY_VAR39', '', 'w'). Not used.
        pos = self.spec_basename_entry.index(INSERT)
        basename = utils.rm_reserved_chars(self.spec_basename_entry.get())
        basename = basename.strip("/").strip("\\")
        self.spec_basename_entry.delete(0, "end")
        self.spec_basename_entry.insert(0, basename)
        self.spec_basename_entry.icursor(pos)

    def validate_startnum(self, *args):
        # pylint: disable = unused-argument
        # args contains a tuple of tkinter pyvars. e.g. ('PY_VAR39', '', 'w'). Not used.
        pos = self.spec_startnum_entry.index(INSERT)
        num = utils.numbers_only(self.spec_startnum_entry.get())
        if len(num) > self.config_info.num_len:
            num = num[0 : self.config_info.num_len]
        if len(num) < len(self.spec_startnum_entry.get()):
            pos = pos - 1
        self.spec_startnum_entry.delete(0, "end")
        self.spec_startnum_entry.insert(0, num)
        self.spec_startnum_entry.icursor(pos)

    @staticmethod
    def validate_sample_name(name):
        name = name.replace("(", "").replace(")", "").replace("i=", "i").replace("e=", "e").replace(":", "")
        return name

    # motor_az input from -90 to 270
    # science az from 0 to 179.
    # az=180, i=50 is the same position as az=0, i=-50
    def motor_pos_to_science_pos(self, motor_i, motor_e, motor_az):
        if motor_az < self.min_motor_az:
            print("UNEXPECTED AZ: " + str(motor_az))
        if motor_az > self.max_motor_az:
            print("UNEXPECTED AZ: " + str(motor_az))
        science_i = motor_i
        science_e = motor_e
        science_az = motor_az

        if motor_az >= 180:
            science_az -= 180
            science_i = -1 * science_i
        if motor_az < 0:
            science_az += 180
            science_i = -1 * science_i

        return science_i, science_e, science_az

    # get the point on the emission arm closest to intersecting the light source
    # az is the difference between the two, as shown in the visualization

    def validate_distance(self, i: int, e: int, az: int):
        closest_dist = utils.get_phase_angle(i, e, az)
        return closest_dist >= self.required_angular_separation

    def clear(self):
        if self.manual_automatic.get() == 0:
            self.unfreeze()
            self.active_incidence_entries[0].delete(0, "end")
            self.active_emission_entries[0].delete(0, "end")
            self.active_azimuth_entries[0].delete(0, "end")
            self.sample_label_entries[self.current_sample_gui_index].delete(0, "end")

    def next_in_queue(self):
        function_dict = self.queue[0]
        for func in function_dict:
            args = function_dict[func]
            func(*args)

    def refresh(self):
        time.sleep(0.25)
        self.goniometer_view.flip()
        self.master.update()

    def resize(
        self, window=None
    ):  # Resize the console and goniometer view frames to be proportional sizes, and redraw the goniometer.
        if window is None:
            window = utils.PretendEvent(self.master, self.master.winfo_width(), self.master.winfo_height())
        if window.widget == self.master:
            try:
                console_height = int(window.height / 3) + 10
                if console_height < 200:
                    console_height = 200
                goniometer_height = window.height - console_height + 10
                self.goniometer_view.double_embed.configure(height=goniometer_height)
                self.console.console_frame.configure(height=console_height)
                self.view_notebook.configure(height=goniometer_height)
                self.plotter.set_height(goniometer_height)

                thread = Thread(
                    target=self.refresh
                )  # I don't understand why this is needed, but things don't seem to get drawn right without it.
                thread.start()

                self.goniometer_view.draw_side_view(
                    window.width - self.control_frame.winfo_width() - 2, goniometer_height - 10
                )
                self.goniometer_view.flip()
                self.master.update()
            except (AttributeError, TclError):
                # Happens when the program is just starting up and there is no view yet
                pass
            except ValueError:
                pass

    def complete_queue_item(self):
        self.queue.pop(0)

    def rm_current(self):
        self.spec_commander.delete_spec(
            self.spec_save_dir_entry.get(), self.spec_basename_entry.get(), self.spec_startnum_entry.get()
        )
        t = utils.BUFFER
        while t > 0:
            if "rmsuccess" in self.spec_listener.queue:
                self.spec_listener.queue.remove("rmsuccess")
                return True
            if "rmfailure" in self.spec_listener.queue:
                self.spec_listener.queue.remove("rmfailure")
                return False
            t = t - utils.INTERVAL
            time.sleep(utils.INTERVAL)
        return False

    def freeze(self):
        # try:
        #     self.plot_manager.plot_top.destroy()
        # except (AttributeError, TclError):
        #     pass
        # try:
        #     self.process_manager.process_top.destroy()
        # except (AttributeError, TclError):
        #     pass
        for button in self.tk_buttons:
            try:
                button.configure(state="disabled")
            except (AttributeError, TclError):
                pass
        for entry in self.entries:
            try:
                entry.configure(state="disabled")
            except (AttributeError, TclError):
                pass
        for radio in self.radiobuttons:
            try:
                radio.configure(state="disabled")
            except (AttributeError, TclError):
                pass

        for button in self.tk_check_buttons:
            try:
                button.configure(state="disabled")
            except (AttributeError, TclError):
                pass

        for menu in self.option_menus:
            try:
                menu.configure(state="disabled")
            except (AttributeError, TclError):
                pass

        self.menubar.entryconfig("Settings", state="disabled")
        self.filemenu.entryconfig(0, state=DISABLED)
        self.filemenu.entryconfig(1, state=DISABLED)
        self.console.console_entry.configure(state="disabled")
        self.frozen = True

    def unfreeze(self):
        self.console.console_entry.configure(state="normal")
        self.menubar.entryconfig("Settings", state="normal")
        self.filemenu.entryconfig(0, state=NORMAL)
        self.filemenu.entryconfig(1, state=NORMAL)
        for button in self.tk_buttons:
            try:
                button.configure(state="normal")
            except (AttributeError, TclError):
                pass
        for entry in self.entries:
            try:
                entry.configure(state="normal")
            except (AttributeError, TclError):
                pass
        for radio in self.radiobuttons:
            try:
                radio.configure(state="normal")
            except (AttributeError, TclError):
                pass

        for button in self.tk_check_buttons:
            try:
                button.configure(state="normal")
            except (AttributeError, TclError):
                pass

        for menu in self.option_menus:
            try:
                menu.configure(state="normal")
            except (AttributeError, TclError):
                pass

        if self.manual_automatic.get() == 0:
            self.range_radio.configure(state="disabled")
            self.add_geometry_button.configure(state="disabled")
            self.add_sample_button.configure(state="disabled")
            for pos_menu in self.pos_menus:
                pos_menu.configure(state="disabled")

        self.frozen = False

    def log(self, text: str, newline: Optional[bool] = True):
        self.console.log(text, newline)
