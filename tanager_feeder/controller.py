import datetime

import numpy as np
import tkinter as tk

from tanager_feeder.goniometer_view import GoniometerView
from tanager_feeder.plotter import Plotter
from tanager_feeder.commanders.spec_commander import SpecCommander
from tanager_feeder.commanders.pi_commander import PiCommander






class Controller():
    def __init__(self, connection_tracker, config_info):
        self.connection_tracker = connection_tracker
        self.config_info = config_info

        self.spec_listener = SpecListener(connection_tracker)
        self.spec_listener.set_controller(self)
        self.spec_listener.start()

        self.pi_listener = PiListener(connection_tracker)
        self.pi_listener.set_controller(self)
        self.pi_listener.start()

        self.spec_commander = SpecCommander(self.connection_tracker.spec_ip, self.spec_listener)
        self.pi_commander = PiCommander(self.connection_tracker.pi_ip, self.pi_listener)

        self.remote_directory_worker = RemoteDirectoryWorker(self.spec_commander, self.spec_listener)

        self.local_config_loc = config_info.local_config_loc
        self.global_config_loc = config_info.global_config_loc
        self.opsys = config_info.opsys

        # The queue is a list of dictionaries commands:parameters
        # The commands are supposed to be executed in order, assuming each one succeeds.
        # CommandHandlers tell the controller when it's time to do the next one
        self.queue = []

        # One wait dialog open at a time. CommandHandlers check whether to use an existing one or make a new one.
        self.wait_dialog = None

        self.min_science_i = -70
        self.max_science_i = 70
        self.min_motor_i = -90
        self.max_motor_i = 90
        self.science_i = None
        self.motor_i = None
        self.final_i = None
        self.i_interval = None

        self.min_science_e = -70
        self.max_science_e = 70
        self.min_motor_e = -90
        self.max_motor_e = 90
        self.science_e = None  # current emission angle
        self.motor_e = None
        self.final_e = None
        self.e_interval = None

        self.min_science_az = 0
        self.max_science_az = 179
        self.min_motor_az = -179
        self.max_motor_az = 270
        self.science_az = None  # current azimuth angle
        self.motor_az = None
        self.final_az = None
        self.az_interval = None

        self.required_angular_separation = 10
        self.reversed_goniometer = False
        self.text_only = False  # for running scripts.

        # cmds the user has entered into the console. Allows scrolling back and forth through commands by using up and down arrows.
        self.user_cmds = []
        self.user_cmd_index = 0
        # self.cmd_complete=False
        self.script_failed = False
        self.num_samples = 5

        self.script_running = False
        self.white_referencing = False
        self.overwrite_all = False  # User can say yes to all for overwriting files.

        self.audio_signals = False

        # These will get set via user input.
        self.spec_save_path = ''
        self.spec_basename = ''
        self.spec_num = None
        self.spec_config_count = None
        self.take_spectrum_with_bad_i_or_e = False
        self.wr_time = None
        self.opt_time = None
        self.angles_change_time = None
        self.current_label = ''

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
        self.sample_frames = []  # Frames holding all of these things. New one gets created each time a sample is added to the GUI.

        self.sample_tray_index = None  # The location of the physical sample tray. This will be an integer -1 to 4 corresponding to wr (-1) or an index in the available_sample_positions (0-4) SORRY!!
        self.current_sample_gui_index = 0  # This might be different from the tray position. For example, if samples are set in trays 2 and 4 only then the gui_index will range from 0 (wr) to 1 (tray 2).
        self.available_sample_positions = ['Sample 1', 'Sample 2', 'Sample 3', 'Sample 4',
                                           'Sample 5']  # All available positions. Does not change.
        self.taken_sample_positions = []  # Filled positions. Changes as samples are added and removed.

        # Yay formatting. Might not work for Macs.
        self.bg = '#333333'
        self.textcolor = 'light gray'
        self.buttontextcolor = 'white'
        self.bd = 2
        self.padx = 3
        self.pady = 3
        self.border_color = 'light gray'
        self.button_width = 15
        self.buttonbackgroundcolor = '#888888'
        self.highlightbackgroundcolor = '#222222'
        self.entry_background = 'light gray'
        if self.opsys == 'Windows':
            self.listboxhighlightcolor = 'darkgray'
        else:
            self.listboxhighlightcolor = 'white'
        self.selectbackground = '#555555'
        self.selectforeground = 'white'
        self.check_bg = '#444444'

        # Tkinter notebook GUI
        self.master = Tk()
        self.master.configure(background=self.bg)

        self.master.title('Control')
        self.master.minsize(1050, 400)
        # When the window closes, send a command to set the geometry to i=0, e=30.
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        #         self.tk_master=self.master #this gets used when deciding whether to open a new master when giving a no connection dialog or something. I can't remember. Maybe could be deleted, but I don't think so

        self.menubar = Menu(self.master)
        # create a pulldown menu, and add it to the menu bar
        self.filemenu = Menu(self.menubar, tearoff=0)
        self.filemenu.add_command(label="Load script", command=self.load_script)
        self.filemenu.add_command(label="Process and export data", command=self.show_process_frame)
        self.filemenu.add_command(label="Plot processed data", command=self.show_plot_frame)
        self.filemenu.add_command(label='Clear plotted data cache', command=self.reset_plot_data)

        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.on_closing)

        self.menubar.add_cascade(label="File", menu=self.filemenu)

        # create more pulldown menus
        editmenu = Menu(self.menubar, tearoff=0)
        editmenu.add_command(label="Failsafes...", command=self.show_settings_frame)
        #         editmenu.add_command(label="Plot settings...", command=self.show_plot_settings_frame)

        self.audiomenu = Menu(editmenu, tearoff=0)
        self.audiomenu.add_command(label='  Enabled', command=self.enable_audio)
        self.audiomenu.add_command(label='X Disabled', command=self.disable_audio)
        editmenu.add_cascade(label="Audio signals", menu=self.audiomenu)

        self.goniometermenu = Menu(editmenu, tearoff=0)
        self.goniometermenu.add_command(label='X Manual', command=lambda: self.set_manual_automatic(force=0))
        self.goniometermenu.add_command(label='  Automatic', command=lambda: self.set_manual_automatic(force=1))
        editmenu.add_cascade(label="Goniometer control", menu=self.goniometermenu)

        self.geommenu = Menu(editmenu, tearoff=0)
        self.geommenu.add_command(label='X Individual', command=lambda: self.set_individual_range(0))
        self.geommenu.add_command(label='  Range (Automatic only)', command=lambda: self.set_individual_range(1),
                                  state=DISABLED)
        editmenu.add_cascade(label='Geometry specification', menu=self.geommenu)

        self.menubar.add_cascade(label="Settings", menu=editmenu)

        helpmenu = Menu(self.menubar, tearoff=0)
        # helpmenu.add_command(label="About", command=hello)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

        # display the menu
        self.master.config(menu=self.menubar)

        self.notebook_frame = Frame(self.master)
        self.notebook_frame.pack(side=LEFT, fill=BOTH, expand=True)
        self.notebook = ttk.Notebook(self.notebook_frame)
        self.tk_buttons = []
        self.entries = []
        self.radiobuttons = []
        self.tk_check_buttons = []
        self.option_menus = []

        self.view_frame = Frame(self.master, width=1800, height=1200, bg=self.bg)
        self.view_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        self.view_notebook_holder = Frame(self.view_frame, width=1800, height=1200)
        self.view_notebook_holder.pack(fill=BOTH, expand=True)
        self.view_notebook = ttk.Notebook(self.view_notebook_holder)
        self.view_notebook.pack()

        self.goniometer_view = GoniometerView(self, self.view_notebook)
        self.view_notebook.bind("<<NotebookTabChanged>>", lambda event: self.goniometer_view.tab_switch(event))
        self.view_notebook.bind('<Button-3>', lambda event: self.plot_right_click(event))

        # The plotter, surprisingly, plots things.
        self.plotter = Plotter(self, self.get_dpi(), [self.global_config_loc + 'color_config.mplstyle',
                                                      self.global_config_loc + 'size_config.mplstyle'])

        # The commander is in charge of sending all the commands for the spec compy to read
        # If the user has saved spectra with this program before, load in their previously used directories.
        self.process_input_dir = ''
        self.process_output_dir = ''
        try:
            with open(self.local_config_loc + 'process_directories.txt', 'r') as process_config:
                self.proc_local_remote = process_config.readline().strip('\n')
                self.process_input_dir = process_config.readline().strip('\n')
                self.process_output_dir = process_config.readline().strip('\n')
        except:
            with open(self.local_config_loc + 'process_directories.txt', 'w+') as f:
                f.write('remote')
                f.write('C:\\Users\n')
                f.write('C:\\Users\n')
                self.proc_local_remote = 'remote'
                self.proc_input_dir = 'C:\\Users'
                self.proc_output_dir = 'C:\\Users'

        try:
            with open(self.local_config_loc + 'plot_config.txt', 'r') as plot_config:
                self.plot_local_remote = plot_config.readline().strip('\n')
                self.plot_input_file = plot_config.readline().strip('\n')
                self.plot_title = plot_config.readline().strip('\n')
        except:
            with open(self.local_config_loc + 'plot_config.txt', 'w+') as f:
                f.write('remote')
                f.write('C:\\Users\n')
                f.write('C:\\Users\n')

            self.plot_local_remote = 'remote'
            self.plot_title = ''
            self.plot_input_file = 'C:\\Users'

        try:
            with open(self.local_config_loc + 'spec_save.txt', 'r') as spec_save_config:
                self.spec_save_path = spec_save_config.readline().strip('\n')
                self.spec_basename = spec_save_config.readline().strip('\n')
                self.spec_startnum = str(int(spec_save_config.readline().strip('\n')) + 1)
                while len(self.spec_startnum) < NUMLEN:
                    self.spec_startnum = '0' + self.spec_startnum
        except:
            with open(self.local_config_loc + 'spec_save.txt', 'w+') as f:
                f.write('C:\\Users\n')
                f.write('basename\n')
                f.write('-1\n')

                self.spec_save_path = 'C:\\Users'
                self.spec_basename = 'basename'
                self.spec_startnum = '0'
                while len(self.spec_startnum) < NUMLEN:
                    self.spec_startnum = '0' + self.spec_startnum

        try:
            with open(self.local_config_loc + 'script_config.txt', 'r') as script_config:
                self.script_loc = script_config.readline().strip('\n')
        except:
            with open(self.local_config_loc + 'script_config.txt', 'w+') as script_config:
                script_config.write(os.getcwd())
                self.script_loc = os.getcwd()
        self.notebook_frames = []

        self.control_frame = VerticalScrolledFrame(self, self.notebook_frame, bg=self.bg)
        self.control_frame.pack(fill=BOTH, expand=True)

        self.save_config_frame = Frame(self.control_frame.interior, bg=self.bg, highlightthickness=1)
        self.save_config_frame.pack(fill=BOTH, expand=True)
        self.spec_save_label = Label(self.save_config_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                     fg=self.textcolor, text='Raw spectral data save configuration:')
        self.spec_save_label.pack(pady=(15, 5))
        self.spec_save_path_label = Label(self.save_config_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                          fg=self.textcolor, text='Directory:')
        self.spec_save_path_label.pack(padx=self.padx)

        self.spec_save_dir_frame = Frame(self.save_config_frame, bg=self.bg)
        self.spec_save_dir_frame.pack()

        self.spec_save_dir_browse_button = Button(self.spec_save_dir_frame, text='Browse',
                                                  command=self.choose_spec_save_dir)
        self.tk_buttons.append(self.spec_save_dir_browse_button)
        self.spec_save_dir_browse_button.config(fg=self.buttontextcolor,
                                                highlightbackground=self.highlightbackgroundcolor,
                                                bg=self.buttonbackgroundcolor)
        self.spec_save_dir_browse_button.pack(side=RIGHT, padx=(3, 15), pady=(5, 10))

        self.spec_save_dir_var = StringVar()
        self.spec_save_dir_var.trace('w', self.validate_spec_save_dir)
        self.spec_save_dir_entry = Entry(self.spec_save_dir_frame, width=50, bd=self.bd, bg=self.entry_background,
                                         selectbackground=self.selectbackground, selectforeground=self.selectforeground,
                                         textvariable=self.spec_save_dir_var)
        self.entries.append(self.spec_save_dir_entry)
        self.spec_save_dir_entry.insert(0, self.spec_save_path)
        self.spec_save_dir_entry.pack(padx=(15, 5), pady=(5, 10), side=RIGHT)
        self.spec_save_frame = Frame(self.save_config_frame, bg=self.bg)
        self.spec_save_frame.pack()

        self.spec_basename_label = Label(self.spec_save_frame, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                         text='Base name:')
        self.spec_basename_label.pack(side=LEFT, pady=self.pady)

        self.spec_basename_var = StringVar()
        self.spec_basename_var.trace('w', self.validate_basename)
        self.spec_basename_entry = Entry(self.spec_save_frame, width=10, bd=self.bd, bg=self.entry_background,
                                         selectbackground=self.selectbackground, selectforeground=self.selectforeground,
                                         textvariable=self.spec_basename_var)
        self.entries.append(self.spec_basename_entry)
        self.spec_basename_entry.pack(side=LEFT, padx=(5, 5), pady=self.pady)
        self.spec_basename_entry.insert(0, self.spec_basename)

        self.spec_startnum_label = Label(self.spec_save_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                         fg=self.textcolor, text='Number:')
        self.spec_startnum_label.pack(side=LEFT, pady=self.pady)

        self.startnum_var = StringVar()
        self.startnum_var.trace('w', self.validate_startnum)
        self.spec_startnum_entry = Entry(self.spec_save_frame, width=10, bd=self.bd, bg=self.entry_background,
                                         selectbackground=self.selectbackground, selectforeground=self.selectforeground,
                                         textvariable=self.startnum_var)
        self.entries.append(self.spec_startnum_entry)
        self.spec_startnum_entry.insert(0, self.spec_startnum)
        self.spec_startnum_entry.pack(side=RIGHT, pady=self.pady)

        self.instrument_config_frame = Frame(self.control_frame.interior, bg=self.bg, highlightthickness=1)
        self.spec_settings_label = Label(self.instrument_config_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                         fg=self.textcolor, text='Instrument Configuration:')
        self.spec_settings_label.pack(padx=self.padx, pady=(10, 10))
        self.instrument_config_frame.pack(fill=BOTH, expand=True)
        self.i_config_label_entry_frame = Frame(self.instrument_config_frame, bg=self.bg)
        self.i_config_label_entry_frame.pack()
        self.instrument_config_label = Label(self.i_config_label_entry_frame, fg=self.textcolor,
                                             text='Number of spectra to average:', bg=self.bg)
        self.instrument_config_label.pack(side=LEFT, padx=(20, 0))

        self.instrument_config_entry = Entry(self.i_config_label_entry_frame, width=10, bd=self.bd,
                                             bg=self.entry_background, selectbackground=self.selectbackground,
                                             selectforeground=self.selectforeground)
        self.entries.append(self.instrument_config_entry)
        self.instrument_config_entry.insert(0, 200)
        self.instrument_config_entry.pack(side=LEFT)

        self.viewing_geom_options_frame = Frame(self.control_frame.interior, bg=self.bg)

        self.viewing_geom_options_frame_left = Frame(self.viewing_geom_options_frame, bg=self.bg, highlightthickness=1)
        self.viewing_geom_options_frame_left.pack(side=LEFT, fill=BOTH, expand=True)

        self.single_mult_frame = Frame(self.viewing_geom_options_frame, bg=self.bg, highlightthickness=1)
        self.single_mult_frame.pack(side=RIGHT, fill=BOTH, expand=True)
        self.angle_control_label = Label(self.single_mult_frame, text='Geometry specification:      ', bg=self.bg,
                                         fg=self.textcolor)
        self.angle_control_label.pack(padx=(5, 5), pady=(10, 5))

        self.individual_range = IntVar()
        self.individual_radio = Radiobutton(self.single_mult_frame, text='Individual         ', bg=self.bg,
                                            fg=self.textcolor, highlightthickness=0, variable=self.individual_range,
                                            value=0, selectcolor=self.check_bg, command=self.set_individual_range)
        self.radiobuttons.append(self.individual_radio)
        self.individual_radio.pack()

        self.range_radio = Radiobutton(self.single_mult_frame, text='Range with interval\n(Automatic only)', bg=self.bg,
                                       fg=self.textcolor, highlightthickness=0, variable=self.individual_range, value=1,
                                       selectcolor=self.check_bg, command=self.set_individual_range)
        self.radiobuttons.append(self.range_radio)
        self.range_radio.configure(state=DISABLED)
        self.range_radio.pack()

        self.gon_control_label_frame = Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.gon_control_label_frame.pack()
        self.gon_control_label = Label(self.gon_control_label_frame, text='\nGoniometer control:         ', bg=self.bg,
                                       fg=self.textcolor)
        self.gon_control_label.pack(side=LEFT, padx=(10, 5))

        self.manual_radio_frame = Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.manual_radio_frame.pack()
        self.manual_automatic = IntVar()
        self.manual_radio = Radiobutton(self.manual_radio_frame, text='Manual            ', bg=self.bg,
                                        fg=self.textcolor, highlightthickness=0, variable=self.manual_automatic,
                                        value=0, selectcolor=self.check_bg, command=self.set_manual_automatic)
        self.radiobuttons.append(self.manual_radio)
        self.manual_radio.pack(side=LEFT, padx=(10, 10), pady=(5, 5))

        self.automation_radio_frame = Frame(self.viewing_geom_options_frame_left, bg=self.bg)
        self.automation_radio_frame.pack()
        self.automation_radio = Radiobutton(self.automation_radio_frame, text='Automatic         ', bg=self.bg,
                                            fg=self.textcolor, highlightthickness=0, variable=self.manual_automatic,
                                            value=1, selectcolor=self.check_bg, command=self.set_manual_automatic)
        self.radiobuttons.append(self.automation_radio)
        self.automation_radio.pack(side=LEFT, padx=(10, 10))
        self.filler_label = Label(self.viewing_geom_options_frame_left, text='', bg=self.bg)
        self.filler_label.pack()

        self.viewing_geom_frame = Frame(self.control_frame.interior, bg=self.bg, highlightthickness=1)
        self.viewing_geom_frame.pack(fill=BOTH, expand=True)

        self.viewing_geom_options_label = Label(self.viewing_geom_frame, text='Viewing geometry:', fg=self.textcolor,
                                                bg=self.bg)
        self.viewing_geom_options_label.pack(pady=(10, 10))

        self.individual_angles_frame = Frame(self.viewing_geom_frame, bg=self.bg, highlightbackground=self.border_color)
        self.individual_angles_frame.pack()
        self.add_geometry()

        self.range_frame = Frame(self.viewing_geom_frame, padx=self.padx, pady=self.pady, bd=2,
                                 highlightbackground=self.border_color, highlightcolor=self.border_color,
                                 highlightthickness=0, bg=self.bg)
        # self.range_frame.pack()
        self.light_frame = Frame(self.range_frame, bg=self.bg)
        self.light_frame.pack(side=LEFT, padx=(5, 5))
        self.light_label = Label(self.light_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                 text='Incidence angles:')
        self.light_label.pack()

        light_labels_frame = Frame(self.light_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        light_labels_frame.pack(side=LEFT)

        light_start_label = Label(light_labels_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                  text='First:')
        light_start_label.pack(pady=(0, 8), padx=(40, 0))
        light_end_label = Label(light_labels_frame, bg=self.bg, padx=self.padx, pady=self.pady, fg=self.textcolor,
                                text='Last:')
        light_end_label.pack(pady=(0, 5), padx=(40, 0))
        light_increment_label = Label(light_labels_frame, bg=self.bg, padx=self.padx, pady=self.pady, fg=self.textcolor,
                                      text='Increment:')
        light_increment_label.pack(pady=(0, 5), padx=(0, 0))

        light_entries_frame = Frame(self.light_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        light_entries_frame.pack(side=RIGHT)

        self.light_start_entry = Entry(light_entries_frame, width=5, bd=self.bd, bg=self.entry_background,
                                       selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.entries.append(self.light_start_entry)
        self.light_start_entry.pack(padx=self.padx, pady=self.pady)
        self.light_end_entry = Entry(light_entries_frame, width=5, highlightbackground='white', bd=self.bd,
                                     bg=self.entry_background, selectbackground=self.selectbackground,
                                     selectforeground=self.selectforeground)
        self.entries.append(self.light_end_entry)
        self.light_end_entry.pack(padx=self.padx, pady=self.pady)
        self.light_increment_entry = Entry(light_entries_frame, width=5, highlightbackground='white', bd=self.bd,
                                           bg=self.entry_background, selectbackground=self.selectbackground,
                                           selectforeground=self.selectforeground)
        self.entries.append(self.light_increment_entry)
        self.light_increment_entry.pack(padx=self.padx, pady=self.pady)

        detector_frame = Frame(self.range_frame, bg=self.bg)
        detector_frame.pack(side=LEFT)

        detector_label = Label(detector_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                               text='Emission angles:')
        detector_label.pack()

        detector_labels_frame = Frame(detector_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        detector_labels_frame.pack(side=LEFT, padx=(5, 5))

        detector_start_label = Label(detector_labels_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                     fg=self.textcolor, text='First:')
        detector_start_label.pack(pady=(0, 8), padx=(40, 0))
        detector_end_label = Label(detector_labels_frame, bg=self.bg, padx=self.padx, pady=self.pady, fg=self.textcolor,
                                   text='Last:')
        detector_end_label.pack(pady=(0, 5), padx=(40, 0))

        detector_increment_label = Label(detector_labels_frame, bg=self.bg, padx=self.padx, pady=self.pady,
                                         fg=self.textcolor, text='Increment:')
        detector_increment_label.pack(pady=(0, 5), padx=(0, 0))

        detector_entries_frame = Frame(detector_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        detector_entries_frame.pack(side=RIGHT)
        self.detector_start_entry = Entry(detector_entries_frame, bd=self.bd, width=5, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground)
        self.entries.append(self.detector_start_entry)
        self.detector_start_entry.pack(padx=self.padx, pady=self.pady)

        self.detector_end_entry = Entry(detector_entries_frame, bd=self.bd, width=5, highlightbackground='white',
                                        bg=self.entry_background, selectbackground=self.selectbackground,
                                        selectforeground=self.selectforeground)
        self.entries.append(self.detector_end_entry)
        self.detector_end_entry.pack(padx=self.padx, pady=self.pady)

        self.detector_increment_entry = Entry(detector_entries_frame, bd=self.bd, width=5, highlightbackground='white',
                                              bg=self.entry_background, selectbackground=self.selectbackground,
                                              selectforeground=self.selectforeground)
        self.entries.append(self.detector_increment_entry)
        self.detector_increment_entry.pack(padx=self.padx, pady=self.pady)

        self.azimuth_frame = Frame(self.range_frame, bg=self.bg)
        self.azimuth_frame.pack(side=LEFT, padx=(5, 5))
        self.azimuth_label = Label(self.azimuth_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                   text='Azimuth angles:')
        self.azimuth_label.pack()

        azimuth_labels_frame = Frame(self.azimuth_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        azimuth_labels_frame.pack(side=LEFT)

        azimuth_start_label = Label(azimuth_labels_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                    text='First:')
        azimuth_start_label.pack(pady=(0, 8), padx=(40, 0))
        azimuth_end_label = Label(azimuth_labels_frame, bg=self.bg, padx=self.padx, pady=self.pady, fg=self.textcolor,
                                  text='Last:')
        azimuth_end_label.pack(pady=(0, 5), padx=(40, 0))

        azimuth_increment_label = Label(azimuth_labels_frame, bg=self.bg, padx=self.padx, pady=self.pady,
                                        fg=self.textcolor, text='Increment:')
        azimuth_increment_label.pack(pady=(0, 5), padx=(0, 0))

        azimuth_entries_frame = Frame(self.azimuth_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        azimuth_entries_frame.pack(side=RIGHT)

        self.azimuth_start_entry = Entry(azimuth_entries_frame, width=5, bd=self.bd, bg=self.entry_background,
                                         selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.entries.append(self.azimuth_start_entry)
        self.azimuth_start_entry.pack(padx=self.padx, pady=self.pady)

        self.azimuth_end_entry = Entry(azimuth_entries_frame, width=5, highlightbackground='white', bd=self.bd,
                                       bg=self.entry_background, selectbackground=self.selectbackground,
                                       selectforeground=self.selectforeground)
        self.entries.append(self.azimuth_end_entry)
        self.azimuth_end_entry.pack(padx=self.padx, pady=self.pady)
        self.azimuth_increment_entry = Entry(azimuth_entries_frame, width=5, highlightbackground='white', bd=self.bd,
                                             bg=self.entry_background, selectbackground=self.selectbackground,
                                             selectforeground=self.selectforeground)
        self.entries.append(self.azimuth_increment_entry)
        self.azimuth_increment_entry.pack(padx=self.padx, pady=self.pady)

        self.samples_frame = Frame(self.control_frame.interior, bg=self.bg, highlightthickness=1)
        self.samples_frame.pack(fill=BOTH, expand=True)

        self.samples_label = Label(self.samples_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                   text='Samples:')
        self.samples_label.pack(pady=(10, 10))

        self.add_sample()

        self.gen_frame = Frame(self.control_frame.interior, bg=self.bg, highlightthickness=1, pady=10)
        self.gen_frame.pack(fill=BOTH, expand=True)

        self.action_button_frame = Frame(self.gen_frame, bg=self.bg)
        self.action_button_frame.pack()

        self.opt_button = Button(self.action_button_frame, fg=self.textcolor, text='Optimize', padx=self.padx,
                                 pady=self.pady, width=self.button_width, bg='light gray', command=self.opt_button_cmd,
                                 height=2)
        self.tk_buttons.append(self.opt_button)
        self.opt_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                               bg=self.buttonbackgroundcolor)
        self.opt_button.pack(padx=self.padx, pady=self.pady, side=LEFT)
        self.wr_button = Button(self.action_button_frame, fg=self.textcolor, text='White Reference', padx=self.padx,
                                pady=self.pady, width=self.button_width, bg='light gray', command=self.wr_button_cmd,
                                height=2)
        self.tk_buttons.append(self.wr_button)
        self.wr_button.pack(padx=self.padx, pady=self.pady, side=LEFT)
        self.wr_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                              bg=self.buttonbackgroundcolor)

        self.spec_button = Button(self.action_button_frame, fg=self.textcolor, text='Take Spectrum', padx=self.padx,
                                  pady=self.pady, width=self.button_width, height=2, bg='light gray',
                                  command=self.spec_button_cmd)
        self.tk_buttons.append(self.spec_button)
        self.spec_button.pack(padx=self.padx, pady=self.pady, side=LEFT)
        self.spec_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                bg=self.buttonbackgroundcolor)

        self.acquire_button = Button(self.action_button_frame, fg=self.textcolor, text='Acquire Data', padx=self.padx,
                                     pady=self.pady, width=self.button_width, height=2, bg='light gray',
                                     command=self.acquire)
        self.tk_buttons.append(self.acquire_button)
        self.acquire_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                   bg=self.buttonbackgroundcolor)

        # ************************Console********************************
        self.console_frame = Frame(self.view_frame, bg=self.border_color, height=200, highlightthickness=2,
                                   highlightcolor=self.bg)
        self.console_frame.pack(fill=BOTH, expand=True, padx=(1, 1))
        self.console_title_label = Label(self.console_frame, padx=self.padx, pady=self.pady, bg=self.border_color,
                                         fg='black', text='Console', font=("Helvetica", 11))
        self.console_title_label.pack(pady=(5, 5))
        self.text_frame = Frame(self.console_frame)
        self.scrollbar = Scrollbar(self.text_frame)
        self.some_width = self.control_frame.winfo_width()
        self.console_log = Text(self.text_frame, width=self.some_width, bg=self.bg, fg=self.textcolor)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry = Entry(self.console_frame, width=self.some_width, bd=self.bd, bg=self.entry_background,
                                   selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.console_entry.bind("<Return>", self.execute_cmd)
        self.console_entry.bind('<Up>', self.iterate_cmds)
        self.console_entry.bind('<Down>', self.iterate_cmds)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.console_log.pack(fill=BOTH, expand=True)
        self.console_entry.focus()

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

        self.plot_remote = IntVar()
        self.plot_local = IntVar()
        if self.plot_local_remote == 'remote':
            self.plot_remote.set(1)
            self.plot_local.set(0)
        else:
            self.plot_local.set(1)
            self.plot_remote.set(0)

        self.proc_remote = IntVar()
        self.proc_local = IntVar()
        if self.proc_local_remote == 'remote':
            self.proc_remote.set(1)
            self.proc_local.set(0)
        else:
            self.proc_local.set(1)
            self.proc_remote.set(0)

        if not PI_OFFLINE:
            self.set_manual_automatic(force=1)

        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)
        thread = Thread(target=self.bind)
        thread.start()

        thread = Thread(
            target=self.scrollbar_check)  # Waits for everything to get packed, then checks if you need a scrollbar on the control frame.
        thread.start()
        if opsys == 'Windows':
            self.master.wm_state('zoomed')
        self.master.mainloop()

    @property
    def science_i(self):
        return self.__science_i

    @science_i.setter
    def science_i(self, value):
        if value == None:
            self.__science_i = value
        else:
            try:
                self.__science_i = int(value)
            except:
                raise Exception("Invalid science i value")

    @property
    def motor_i(self):
        return self.__motor_i

    @motor_i.setter
    def motor_i(self, value):
        if value == None:
            self.__motor_i = value
        else:
            try:
                self.__motor_i = int(value)
                try:
                    science_i, science_e, science_az = self.motor_pos_to_science_pos(self.__motor_i, self.motor_e,
                                                                                     self.motor_az)
                    self.science_i = science_i
                    self.science_az = science_az
                except:
                    self.science_i = self.__motor_i
            except:
                raise Exception("Invalid motor i value")

    @property
    def science_e(self):
        return self.__science_e

    @science_e.setter
    def science_e(self, value):
        if value == None:
            self.__science_e = value
        else:
            try:
                self.__science_e = int(value)
            except:
                raise Exception("Invalid science e value")

    @property
    def motor_e(self):
        return self.__motor_e

    @motor_e.setter
    def motor_e(self, value):
        if value == None:
            self.__motor_e = value
        else:
            try:
                self.__motor_e = int(value)
                self.science_e = self.__motor_e
            except:
                raise Exception("Invalid motor e value")

    @property
    def science_az(self):
        return self.__science_az

    @science_az.setter
    def science_az(self, value):
        if value == None:
            self.__science_az = value
        else:
            try:
                self.__science_az = int(value)
            except:
                raise Exception("Invalid science az value")

    @property
    def motor_az(self):
        return self.__motor_az

    @motor_az.setter
    def motor_az(self, value):
        if value == None:
            self.__motor_az = value
        else:
            try:
                self.__motor_az = int(value)
                try:
                    science_i, science_e, science_az = self.motor_pos_to_science_pos(self.motor_i, self.motor_e,
                                                                                     self.__motor_az)
                    self.science_i = science_i
                    self.science_az = science_az
                except:
                    if 0 <= value and 180 > value:
                        self.science_az = value
                    elif value < 0:
                        self.science_az = value + 180
                    else:
                        self.science_az = value - 180
            except:
                raise Exception("Invalid motor az value")

    def scrollbar_check(self):
        time.sleep(0.5)
        self.control_frame.update()

    # ********************** Process frame ******************************
    # called when user goes to File > Process and export data
    def show_process_frame(self):

        self.process_top = Toplevel(self.master)
        self.process_top.wm_title('Process Data')
        self.process_frame = Frame(self.process_top, bg=self.bg, pady=15, padx=15)
        self.process_frame.pack()

        self.input_dir_label = Label(self.process_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                     text='Raw spectral data input directory:')
        self.input_dir_label.pack(padx=self.padx, pady=(10, 5))

        self.input_frame = Frame(self.process_frame, bg=self.bg)
        self.input_frame.pack()

        self.process_input_browse_button = Button(self.input_frame, text='Browse',
                                                  command=self.choose_process_input_dir)
        self.process_input_browse_button.config(fg=self.buttontextcolor,
                                                highlightbackground=self.highlightbackgroundcolor,
                                                bg=self.buttonbackgroundcolor)
        self.process_input_browse_button.pack(side=RIGHT, padx=self.padx)
        self.tk_buttons.append(self.process_input_browse_button)

        self.input_dir_var = StringVar()
        self.input_dir_var.trace('w', self.validate_input_dir)

        self.input_dir_entry = Entry(self.input_frame, width=50, bd=self.bd, textvariable=self.input_dir_var,
                                     bg=self.entry_background, selectbackground=self.selectbackground,
                                     selectforeground=self.selectforeground)
        self.input_dir_entry.insert(0, self.process_input_dir)
        self.input_dir_entry.pack(side=RIGHT, padx=self.padx, pady=self.pady)
        self.entries.append(self.input_dir_entry)

        self.proc_local_remote_frame = Frame(self.process_frame, bg=self.bg)
        self.proc_local_remote_frame.pack()

        self.output_dir_label = Label(self.proc_local_remote_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                      fg=self.textcolor, text='Processed data output directory:')
        self.output_dir_label.pack(padx=self.padx, pady=(10, 5), side=LEFT)

        self.proc_local_check = Checkbutton(self.proc_local_remote_frame, fg=self.textcolor, text=' Local',
                                            selectcolor=self.check_bg, bg=self.bg, pady=self.pady,
                                            variable=self.proc_local, highlightthickness=0, highlightbackground=self.bg,
                                            command=self.local_process_cmd)
        self.proc_local_check.pack(side=LEFT, pady=(5, 0), padx=(5, 5))
        if self.proc_local_remote == 'local':
            self.proc_local_check.select()
        self.tk_check_buttons.append(self.proc_local_check)

        self.proc_remote_check = Checkbutton(self.proc_local_remote_frame, fg=self.textcolor, text=' Remote',
                                             bg=self.bg, pady=self.pady, highlightthickness=0,
                                             variable=self.proc_remote, command=self.remote_process_cmd,
                                             selectcolor=self.check_bg)
        self.proc_remote_check.pack(side=LEFT, pady=(5, 0), padx=(5, 5))
        if self.proc_local_remote == 'remote':
            self.proc_remote_check.select()
        self.tk_check_buttons.append(self.proc_remote_check)

        self.process_output_frame = Frame(self.process_frame, bg=self.bg)
        self.process_output_frame.pack(pady=(5, 10))
        self.process_output_browse_button = Button(self.process_output_frame, text='Browse',
                                                   command=self.choose_process_output_dir)
        self.process_output_browse_button.config(fg=self.buttontextcolor,
                                                 highlightbackground=self.highlightbackgroundcolor,
                                                 bg=self.buttonbackgroundcolor)
        self.process_output_browse_button.pack(side=RIGHT, padx=self.padx)
        self.tk_buttons.append(self.process_output_browse_button)

        self.output_dir_entry = Entry(self.process_output_frame, width=50, bd=self.bd, bg=self.entry_background,
                                      selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.output_dir_entry.insert(0, self.process_output_dir)
        self.output_dir_entry.pack(side=RIGHT, padx=self.padx, pady=self.pady)
        self.entries.append(self.output_dir_entry)

        self.output_file_label = Label(self.process_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                       fg=self.textcolor, text='Output file name:')
        self.output_file_label.pack(padx=self.padx, pady=self.pady)
        self.output_file_entry = Entry(self.process_frame, width=50, bd=self.bd, bg=self.entry_background,
                                       selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.output_file_entry.pack()
        self.entries.append(self.output_file_entry)

        self.process_check_frame = Frame(self.process_frame, bg=self.bg)
        self.process_check_frame.pack(pady=(15, 5))
        self.process_save_dir = IntVar()
        self.process_save_dir_check = Checkbutton(self.process_check_frame, selectcolor=self.check_bg,
                                                  fg=self.textcolor, text='Save file configuration', bg=self.bg,
                                                  pady=self.pady, highlightthickness=0, variable=self.process_save_dir)
        self.process_save_dir_check.select()

        self.process_button_frame = Frame(self.process_frame, bg=self.bg)
        self.process_button_frame.pack()
        self.process_button = Button(self.process_button_frame, fg=self.textcolor, text='Process', padx=self.padx,
                                     pady=self.pady, width=int(self.button_width * 1.3), bg='light gray',
                                     command=self.process_cmd)
        self.process_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                   bg=self.buttonbackgroundcolor)
        self.process_button.pack(padx=(15, 15), side=LEFT)
        self.tk_buttons.append(self.process_button)

        self.process_close_button = Button(self.process_button_frame, fg=self.buttontextcolor,
                                           highlightbackground=self.highlightbackgroundcolor, text='Close',
                                           padx=self.padx, pady=self.pady, width=int(self.button_width * 1.3),
                                           bg=self.buttonbackgroundcolor, command=self.close_process)
        self.process_close_button.pack(padx=(15, 15), side=LEFT)
        self.tk_buttons.append(self.process_close_button)

    # Closes process frame
    def close_process(self):
        self.process_top.destroy()

    def enable_audio(self):
        self.audio_signals = True
        self.audiomenu.entryconfigure(0, label='X Enabled')
        self.audiomenu.entryconfigure(1, label='  Disabled')

    def disable_audio(self):
        self.audio_signals = False
        self.audiomenu.entryconfigure(0, label='  Enabled')
        self.audiomenu.entryconfigure(1, label='X Disabled')

    def show_plot_settings_frame(self):
        pass

    # Show failsafes settings frame
    def show_settings_frame(self):
        self.settings_top = Toplevel(self.master)
        self.settings_top.wm_title('Failsafe Settings')
        self.settings_frame = Frame(self.settings_top, bg=self.bg, pady=2 * self.pady, padx=15)
        self.settings_frame.pack()

        self.failsafe_title_frame = Frame(self.settings_frame, bg=self.bg)
        self.failsafe_title_frame.pack(pady=(10, 0), fill=X, expand=True)
        self.failsafe_label0 = Label(self.failsafe_title_frame, fg=self.textcolor,
                                     text='Failsafes:                                                                      ',
                                     bg=self.bg)
        self.failsafe_label0.pack(side=LEFT)

        self.failsafe_frame = Frame(self.settings_frame, bg=self.bg, pady=self.pady)
        self.failsafe_frame.pack(fill=BOTH, expand=True, padx=(10, 10))

        self.wr_failsafe_check_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wr_failsafe_check_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.wrfailsafe_check = Checkbutton(self.wr_failsafe_check_frame, fg=self.textcolor,
                                            text='Prompt if no white reference has been taken.', bg=self.bg,
                                            pady=self.pady, highlightthickness=0, variable=self.wrfailsafe,
                                            selectcolor=self.check_bg)
        self.wrfailsafe_check.pack(side=LEFT)
        if self.wrfailsafe.get():
            self.wrfailsafe_check.select()

        self.wr_timeout_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wr_timeout_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.wr_timeout_label = Label(self.wr_timeout_frame, fg=self.textcolor, text='Timeout (minutes):', bg=self.bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(20, 0))
        self.wr_timeout_entry = Entry(self.wr_timeout_frame, bd=self.bd, width=10, bg=self.entry_background,
                                      selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.wr_timeout_entry.pack(side=LEFT, padx=(0, 20))
        self.wr_timeout_entry.insert(0, '8')

        self.optfailsafe_check_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.optfailsafe_check_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.optfailsafe_check = Checkbutton(self.optfailsafe_check_frame, fg=self.textcolor,
                                             text='Prompt if the instrument has not been optimized.', bg=self.bg,
                                             pady=self.pady, highlightthickness=0, selectcolor=self.check_bg,
                                             variable=self.optfailsafe)
        self.optfailsafe_check.pack(side=LEFT)
        if self.optfailsafe.get():
            self.optfailsafe_check.select()

        self.opt_timeout_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.opt_timeout_frame.pack(pady=self.pady, fill=X, expand=True, padx=(20, 5))
        self.opt_timeout_label = Label(self.opt_timeout_frame, fg=self.textcolor, text='Timeout (minutes):', bg=self.bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(20, 0))
        self.opt_timeout_entry = Entry(self.opt_timeout_frame, bd=self.bd, width=10, bg=self.entry_background,
                                       selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.opt_timeout_entry.pack(side=LEFT, padx=(0, 20))
        self.opt_timeout_entry.insert(0, '60')
        self.filler_label = Label(self.opt_timeout_frame, bg=self.bg, fg=self.textcolor, text='              ')
        self.filler_label.pack(side=LEFT)

        self.angles_failsafe_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.angles_failsafe_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.angles_failsafe_check = Checkbutton(self.angles_failsafe_frame, fg=self.textcolor,
                                                 text='Check validity of emission and incidence angles.', bg=self.bg,
                                                 pady=self.pady, highlightthickness=0, selectcolor=self.check_bg,
                                                 variable=self.angles_failsafe)
        # self.angles_failsafe_check.pack(pady=(6,5),side=LEFT,padx=(0,20))
        if self.angles_failsafe.get():
            self.angles_failsafe_check.select()

        self.label_failsafe_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.label_failsafe_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.label_failsafe_check = Checkbutton(self.label_failsafe_frame, fg=self.textcolor,
                                                text='Require a label for each spectrum.', bg=self.bg, pady=self.pady,
                                                highlightthickness=0, selectcolor=self.check_bg,
                                                variable=self.labelfailsafe)
        self.label_failsafe_check.pack(pady=(6, 5), side=LEFT, padx=(0, 20))
        if self.labelfailsafe.get():
            self.label_failsafe_check.select()

        self.wr_angles_failsafe_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wr_angles_failsafe_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.wr_angles_failsafe_check = Checkbutton(self.wr_angles_failsafe_frame, selectcolor=self.check_bg,
                                                    fg=self.textcolor,
                                                    text='Require a new white reference at each viewing geometry             ',
                                                    bg=self.bg, pady=self.pady, highlightthickness=0,
                                                    variable=self.wr_angles_failsafe)
        self.wr_angles_failsafe_check.pack(pady=(6, 5), side=LEFT)
        if self.wr_angles_failsafe.get():
            self.wr_angles_failsafe_check.select()

        self.wrap_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wrap_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.anglechangefailsafe_check = Checkbutton(self.wrap_frame, selectcolor=self.check_bg, fg=self.textcolor,
                                                     text='Remind me to check the goniometer if the viewing geometry changes.',
                                                     bg=self.bg, pady=self.pady, highlightthickness=0,
                                                     variable=self.anglechangefailsafe)
        # self.anglechangefailsafe_check.pack(pady=(6,5),side=LEFT)#side=LEFT, pady=self.pady)
        # if self.anglechangefailsafe.get():
        #   self.anglechangefailsafe_check.select()

        self.failsafes_ok_button = Button(self.failsafe_frame, text='Ok', command=self.settings_top.destroy)
        self.failsafes_ok_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                        bg=self.buttonbackgroundcolor, width=15)
        self.failsafes_ok_button.pack(pady=self.pady)
        self.settings_top.resizable(False, False)

    # ********************** Plot frame ******************************
    def show_plot_frame(self):
        self.plot_top = Toplevel(self.master)
        self.plot_top.wm_title('Plot')
        self.plot_frame = Frame(self.plot_top, bg=self.bg, pady=2 * self.pady, padx=15)
        self.plot_frame.pack()

        self.plot_title_label = Label(self.plot_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                                      text='Plot title:')
        self.plot_title_label.pack(padx=self.padx, pady=(15, 5))
        self.plot_title_entry = Entry(self.plot_frame, width=50, bd=self.bd, bg=self.entry_background,
                                      selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.plot_title_entry.insert(0, self.plot_title)
        self.plot_title_entry.pack(pady=(5, 20))
        self.plot_local_remote_frame = Frame(self.plot_frame, bg=self.bg)
        self.plot_local_remote_frame.pack()

        self.plot_input_dir_label = Label(self.plot_local_remote_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                          fg=self.textcolor, text='Path to .csv file:')
        self.plot_input_dir_label.pack(side=LEFT, padx=self.padx, pady=self.pady)

        self.plot_local_check = Checkbutton(self.plot_local_remote_frame, fg=self.textcolor, text=' Local',
                                            selectcolor=self.check_bg, bg=self.bg, pady=self.pady,
                                            variable=self.plot_local, highlightthickness=0, highlightbackground=self.bg,
                                            command=self.local_plot_cmd)
        self.plot_local_check.pack(side=LEFT, pady=(5, 5), padx=(5, 5))

        self.plot_remote_check = Checkbutton(self.plot_local_remote_frame, fg=self.textcolor, text=' Remote',
                                             bg=self.bg, pady=self.pady, highlightthickness=0,
                                             variable=self.plot_remote, command=self.remote_plot_cmd,
                                             selectcolor=self.check_bg)
        self.plot_remote_check.pack(side=LEFT, pady=(5, 5), padx=(5, 5))

        # controls whether the file being plotted is looked for locally or on the spectrometer computer
        if self.plot_local_remote == 'remote':
            self.plot_remote_check.select()
            self.plot_local_check.deselect()
        if self.plot_local_remote == 'local':
            self.plot_local_check.select()
            self.plot_remote_check.deselect()

        self.plot_file_frame = Frame(self.plot_frame, bg=self.bg)
        self.plot_file_frame.pack(pady=(5, 10))
        self.plot_file_browse_button = Button(self.plot_file_frame, text='Browse', command=self.choose_plot_file)
        self.plot_file_browse_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                            bg=self.buttonbackgroundcolor)
        self.plot_file_browse_button.pack(side=RIGHT, padx=self.padx)

        self.plot_input_dir_entry = Entry(self.plot_file_frame, width=50, bd=self.bd, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground)
        self.plot_input_dir_entry.insert(0, self.plot_input_file)
        self.plot_input_dir_entry.pack(side=RIGHT)

        self.plot_button_frame = Frame(self.plot_frame, bg=self.bg)
        self.plot_button_frame.pack()

        self.plot_button = Button(self.plot_button_frame, fg=self.textcolor, text='Plot', padx=self.padx,
                                  pady=self.pady, width=int(self.button_width * 1.3), bg='light gray',
                                  command=self.plot)
        self.plot_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                bg=self.buttonbackgroundcolor)
        self.plot_button.pack(side=LEFT, pady=(20, 20), padx=(15, 15))

        self.process_close_button = Button(self.plot_button_frame, fg=self.buttontextcolor,
                                           highlightbackground=self.highlightbackgroundcolor, text='Close',
                                           padx=self.padx, pady=self.pady, width=int(self.button_width * 1.3),
                                           bg=self.buttonbackgroundcolor, command=self.close_plot)
        self.process_close_button.pack(pady=(20, 20), padx=(15, 15), side=LEFT)

    def close_plot(self):
        self.plot_top.destroy()

    def bind(
            self):  # This is probably important but I don't remember exactly how it works. Somethign to do with setting up the GUI.
        self.master.bind("<Configure>", self.resize)
        time.sleep(0.2)
        window = PretendEvent(self.master, self.master.winfo_width(), self.master.winfo_height())
        self.resize(window)
        time.sleep(0.2)

        if not SPEC_OFFLINE:
            self.log('Spec compy connected.')
        else:
            self.log('Spec compy not connected. Working offline. Restart to collect spectral data.')
        if not PI_OFFLINE:
            self.log('Raspberry pi connected.')
        else:
            self.log('Raspberry pi not connected. Working offline. Restart to use automation features.')

    def on_closing(self):
        self.goniometer_view.quit()
        self.master.destroy()

    # Toggle back and forth between saving your processed data remotely or locally
    def local_process_cmd(self):
        if self.proc_local.get() and not self.proc_remote.get():
            return
        elif self.proc_remote.get() and not self.proc_local.get():
            return
        elif not self.proc_remote.get():
            self.proc_remote_check.select()
        else:
            self.proc_remote_check.deselect()
            self.proc_local_remote = 'local'
            self.output_dir_entry.delete(0, 'end')

    # Toggle back and forth between saving your processed data remotely or locally
    def remote_process_cmd(self):
        if self.proc_local.get() and not self.proc_remote.get():
            return
        elif self.proc_remote.get() and not self.proc_local.get():
            return
        elif not self.proc_local.get():
            self.proc_local_check.select()

        else:
            self.proc_local_check.deselect()
            self.proc_local_remote = 'remote'
            self.output_dir_entry.delete(0, 'end')

    # Toggle back and forth between plotting your data from a remote or local file
    def local_plot_cmd(self):
        if self.plot_local.get() and not self.plot_remote.get():
            return
        elif self.plot_remote.get() and not self.plot_local.get():
            return
        elif not self.plot_remote.get():
            self.plot_remote_check.select()
        else:
            self.plot_remote_check.deselect()

    # Toggle back and forth between plotting your data from a remote or local file
    def remote_plot_cmd(self):
        if self.plot_local.get() and not self.plot_remote.get():
            return
        elif self.plot_remote.get() and not self.plot_local.get():
            return
        elif not self.plot_local.get():
            self.plot_local_check.select()
        else:
            self.plot_local_check.deselect()

    def load_script(self):
        self.script_running = True
        self.script_failed = False
        script_file = askopenfilename(initialdir=self.script_loc, title='Select script')
        if script_file == '':
            self.script_running = False
            self.queue = []
            return
        self.queue = []
        with open(self.local_config_loc + 'script_config.txt', 'w') as script_config:
            dir = ''
            if self.opsys == 'Linux' or self.opsys == 'Mac':
                dir = '/'.join(script_file.split('/')[0:-1])
            else:
                dir = '\\'.join(script_file.split('\\')[0:-1])

            self.script_loc = dir
            script_config.write(dir)

        with open(script_file, 'r') as script:
            cmd = script.readline().strip('\n')
            success = True
            while cmd != '':  # probably just cmd!=''.
                print(cmd)
                self.queue.append({self.next_script_line: [cmd]})
                cmd = script.readline().strip('\n')
                continue
        self.queue.append({self.next_script_line: ['end file']})
        self.next_in_queue()

    def next_script_line(self, cmd):
        self.script_running = True
        if cmd == 'end file':
            self.log('Script complete')
            self.script_running = False
            self.queue = []
        if self.script_failed:
            self.log('Exiting')
            self.queue = []
        else:
            print(cmd)
            self.unfreeze()
            self.console_entry.delete(0, 'end')
            self.console_entry.insert(0, cmd)
            self.freeze()
            success = self.execute_cmd('event!')
            if success == False:
                self.log('Exiting.')

    def move_sample():
        self.pi_commander.move_sample()

    # use this to make plots - matplotlib works in inches but we want to use pixels.
    def get_dpi(self):
        MM_TO_IN = 1 / 25.4
        pxw = self.master.winfo_screenwidth()
        inw = self.master.winfo_screenmmwidth() * MM_TO_IN
        return pxw / inw

    def opt_old(self, override=False):

        try:
            new_spec_config_count = int(self.instrument_config_entry.get())
            if new_spec_config_count < 1 or new_spec_config_count > 32767:
                raise (Exception)
        except:
            dialog = ErrorDialog(self,
                                 label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return

        ready = self.setup_RS3_config({self.opt: [
            True]})  # Since we want to make sure optimization times are logged in the current folder, we do all the setup checks before optimizing even though no data gets saved.

        if ready:  # If we don't still need to set save config or configure instrument before optimizing

            self.spec_commander.optimize()
            handler = OptHandler(self)

    # when operating in manual mode, check validity of viewing geom when the user clicks buttons. If valid, update graphic and self.i and self.e before moving on to other checks. Return any warnings.
    def check_viewing_geom_for_manual_operation(self):
        warnings = ''

        valid_i = validate_int_input(self.incidence_entries[0].get(), -90, 90)
        if valid_i:
            if str(self.science_i) != self.incidence_entries[0].get():
                self.angles_change_time = time.time()
            self.motor_i = int(self.incidence_entries[0].get())

        else:
            warnings += 'The incidence angle is invalid (Min:' + str(-90) + ', Max:' + str(90) + ').\n\n'

        valid_e = validate_int_input(self.emission_entries[0].get(), -90, 90)
        if valid_e:
            if str(self.science_e) != self.emission_entries[0].get():
                self.angles_change_time = time.time()
            self.motor_e = int(self.emission_entries[0].get())
        else:
            warnings += 'The emission angle is invalid (Min:' + str(-90) + ', Max:' + str(90) + ').\n\n'

        valid_az = validate_int_input(self.azimuth_entries[0].get(), 0, 179)
        if valid_az:
            if str(self.science_az) != self.azimuth_entries[0].get():
                self.angles_change_time = time.time()
            self.motor_az = int(self.azimuth_entries[0].get())
        else:
            warnings += 'The azimuth angle is invalid (Min:' + str(0) + ', Max:' + str(179) + ').\n\n'

        valid_separation = self.validate_distance(self.incidence_entries[0].get(), self.emission_entries[0].get(),
                                                  self.azimuth_entries[0].get())
        if valid_e and valid_i and valid_az and not valid_separation:
            warnings += 'Light source and detector should be at least ' + str(
                self.required_angular_separation) + ' degrees apart.\n\n'
        #             self.set_and_animate_geom()

        return warnings

    # Check whether the current save configuration for raw spectral is different from the last one saved. If it is, send commands to the spec compy telling it so.
    def check_save_config(self):
        new_spec_save_dir = self.spec_save_dir_entry.get()
        new_spec_basename = self.spec_basename_entry.get()
        try:
            new_spec_num = int(self.spec_startnum_entry.get())
        except:
            return 'invalid'

        if new_spec_save_dir == '' or new_spec_basename == '' or new_spec_num == '':
            return 'invalid'

        if new_spec_save_dir != self.spec_save_path or new_spec_basename != self.spec_basename or self.spec_num == None or new_spec_num != self.spec_num:
            return 'not_set'
        else:
            return 'set'

    def check_mandatory_input(self):
        save_config_status = self.check_save_config()
        if save_config_status == 'invalid':
            dialog = ErrorDialog(self, label='Error: Please enter a valid save configuration.')
            return False

        try:
            new_spec_config_count = int(self.instrument_config_entry.get())
            if new_spec_config_count < 1 or new_spec_config_count > 32767:
                raise (Exception)
        except:
            dialog = ErrorDialog(self,
                                 label='Error: Invalid number of spectra to average.\nEnter a value from 1 to 32767')
            return False

        if self.manual_automatic.get() == 1:  # 0 is manual, 1 is automatic
            for index in range(len(self.active_incidence_entries)):
                i = self.active_incidence_entries[index].get()
                e = self.active_emission_entries[index].get()
                az = self.active_azimuth_entries[index].get()
                valid_i = validate_int_input(i, self.min_science_i, self.max_science_i)
                valid_e = validate_int_input(e, self.min_science_e, self.max_science_e)
                valid_az = validate_int_input(az, self.min_science_az, self.max_science_az)
                if not valid_i or not valid_e or not valid_az:
                    dialog = ErrorDialog(self, label='Error: Invalid viewing geometry:\n\nincidence = ' + str(
                        i) + '\nemission = ' + str(e) + '\nazimuth = ' + str(az), width=300, height=130)
                    return False
                elif not self.validate_distance(i, e, az):
                    dialog = ErrorDialog(self,
                                         label='Error: Due to geometric constraints on the goniometer,\nincidence must be at least ' + str(
                                             self.required_angular_separation) + ' degrees different than emission.',
                                         width=300, height=130)
                    return False

        return True

    # If the user has failsafes activated, check that requirements are met. Always require a valid number of spectra.
    # Different requirements are checked depending on what the function func is that will be called next (opt, wr, take spectrum, acquire)
    def check_optional_input(self, func, args=[], warnings=''):
        label = warnings
        now = int(time.time())
        incidence = self.incidence_entries[0].get()
        emission = self.emission_entries[0].get()
        azimuth = self.azimuth_entries[0].get()

        if self.manual_automatic.get() == 0:
            warnings = self.check_viewing_geom_for_manual_operation()
            label += warnings

            if self.optfailsafe.get() and func != self.opt:
                try:
                    opt_limit = int(float(self.opt_timeout_entry.get())) * 60
                except:
                    opt_limit = sys.maxsize
                if self.opt_time == None:
                    label += 'The instrument has not been optimized.\n\n'
                elif now - self.opt_time > opt_limit:
                    minutes = str(int((now - self.opt_time) / 60))
                    seconds = str((now - self.opt_time) % 60)
                    if int(minutes) > 0:
                        label += 'The instrument has not been optimized for ' + minutes + ' minutes ' + seconds + ' seconds.\n\n'
                    else:
                        label += 'The instrument has not been optimized for ' + seconds + ' seconds.\n\n'
                if self.opt_time != None:
                    if self.angles_change_time == None:
                        pass
                    elif self.opt_time < self.angles_change_time:
                        valid_i = validate_int_input(incidence, self.min_science_i, self.max_science_i)
                        valid_e = validate_int_input(emission, self.min_science_e, self.max_science_e)
                        valid_az = validate_int_input(azimuth, self.min_science_az, self.max_science_az)
                        if valid_i and valid_e and valid_az:
                            label += 'The instrument has not been optimized at this geometry.\n\n'

            if self.wrfailsafe.get() and func != self.wr and func != self.opt:

                try:
                    wr_limit = int(float(self.wr_timeout_entry.get())) * 60
                except:
                    wr_limit = sys.maxsize
                if self.wr_time == None:
                    label += 'No white reference has been taken.\n\n'
                elif self.opt_time != None and self.opt_time > self.wr_time:
                    label += 'No white reference has been taken since the instrument was optimized.\n\n'
                elif int(self.instrument_config_entry.get()) != int(self.spec_config_count):
                    label += 'No white reference has been taken while averaging this number of spectra.\n\n'
                elif self.spec_config_count == None:
                    label += 'No white reference has been taken while averaging this number of spectra.\n\n'
                elif now - self.wr_time > wr_limit:
                    minutes = str(int((now - self.wr_time) / 60))
                    seconds = str((now - self.wr_time) % 60)
                    if int(minutes) > 0:
                        label += ' No white reference has been taken for ' + minutes + ' minutes ' + seconds + ' seconds.\n\n'
                    else:
                        label += ' No white reference has been taken for ' + seconds + ' seconds.\n\n'
            if self.wr_angles_failsafe.get() and func != self.wr:

                if self.angles_change_time != None and self.wr_time != None and func != self.opt:
                    if self.angles_change_time > self.wr_time + 1:
                        valid_i = validate_int_input(incidence, self.min_science_i, self.max_science_i)
                        valid_e = validate_int_input(emission, self.min_science_e, self.max_science_e)
                        valid_az = validate_int_input(azimuth, self.min_science_az, self.max_science_az)
                        if valid_i and valid_e:
                            label += ' No white reference has been taken at this viewing geometry.\n\n'
                    # elif str(emission)!=str(self.e) or str(incidence)!=str(self.i):
                    #     label+=' No white reference has been taken at this viewing geometry.\n\n'

        if self.labelfailsafe.get() and func != self.opt and func != self.wr:
            if self.sample_label_entries[self.current_sample_gui_index].get() == '':
                label += 'This sample has no label.\n\n'
        for entry in self.sample_label_entries:
            sample_label = entry.get()
            newlabel = self.validate_sample_name(sample_label)
            if newlabel != sample_label:
                entry.delete(0, 'end')
                if newlabel == '':
                    newlabel = 'sample'

                entry.insert(0, newlabel)
                label += "'" + sample_label + "' is an invalid sample label.\nSample will be labeled as '" + newlabel + "' instead.\n\n"
                self.log(
                    "Warning: '" + sample_label + "' is an invalid sample label. Removing reserved characters and expressions.")

        if label != '':  # if we came up with errors
            title = 'Warning!'

            buttons = {
                'yes': {
                    # if the user says they want to continue anyway, run take spectrum again but this time with override=True
                    func: args
                },
                'no': {}
            }
            label = 'Warning!\n\n' + label
            label += '\nDo you want to continue?'
            dialog = Dialog(self, title, label, buttons)
            return False
        else:  # if there were no errors
            return True

    # Setup gets called after we already know that input is valid, but before we've set up the specrometer control software. If we need to set RS3's save configuration or the instrument configuration (number of spectra to average), it puts those things into the queue saying we will need to do them when we start.
    def setup_RS3_config(self, nextaction):
        # self.check_logfile()
        if self.manual_automatic.get() == 0:
            thread = Thread(target=self.set_and_animate_geom)
            thread.start()

        # Requested save config is guaranteed to be valid because of input checks above.
        print('check save config')
        save_config_status = self.check_save_config()
        print(save_config_status)
        if self.check_save_config() == 'not_set':
            self.complete_queue_item()
            self.queue.insert(0, nextaction)
            self.queue.insert(0, {self.set_save_config: []})
            self.set_save_config()  # self.take_spectrum,[True])
            return False

        # Requested instrument config is guaranteed to be valid because of input checks above.
        new_spec_config_count = int(self.instrument_config_entry.get())
        if self.spec_config_count == None or str(new_spec_config_count) != str(self.spec_config_count):
            self.complete_queue_item()
            self.queue.insert(0, nextaction)
            self.queue.insert(0, {self.configure_instrument: []})
            self.configure_instrument()
            return False

        if True:  # self.spec_save_config.get():
            file = open(self.local_config_loc + 'spec_save.txt', 'w')
            file.write(self.spec_save_dir_entry.get() + '\n')
            file.write(self.spec_basename_entry.get() + '\n')
            file.write(self.spec_startnum_entry.get() + '\n')
            self.process_input_dir = self.spec_save_dir_entry.get()
        return True

    # acquire is called every time opt, wr, or take spectrum buttons are pushed from manual mode
    # also called if acquire button is pushed in automatic mode
    # Action will be either wr, take_spectrum, or opt (manual mode) OR it might just be 'acquire' (automatic mode)
    # For any of these things, we need to validate input.
    def acquire(self, override=False, setup_complete=False, action=None, garbage=False):
        if not setup_complete:
            # Make sure basenum entry has the right number of digits. It is already guaranteed to have no more digits than allowed and to only have numbers.
            start_num = self.spec_startnum_entry.get()
            num_zeros = NUMLEN - len(start_num)
            for _ in range(num_zeros):
                start_num = '0' + start_num
            self.set_text(self.spec_startnum_entry, start_num)

            # Set all entries to active. Viewing geometry information will be pulled from these one at a time. Entries are removed from the active list after the geom info is read.
            self.active_incidence_entries = list(self.incidence_entries)
            self.active_emission_entries = list(self.emission_entries)
            self.active_azimuth_entries = list(self.azimuth_entries)
            self.active_geometry_frames = list(self.geometry_frames)

        range_warnings = ''
        if action == None:  # If this was called by the user clicking acquire. otherwise, it will be take_spectrum or wr?
            action = self.acquire
            self.queue.insert(0, {self.acquire: []})
            if self.individual_range.get() == 1:
                valid_range = self.range_setup(override)
                if not valid_range:
                    return
                elif type(
                        valid_range) == str:  # If there was a warning associated with the input check for the range setup e.g. interval specified as zero, then we'll log this as a warning for the user coming up.
                    range_warnings = valid_range

        if not override:  # If input isn't valid and the user asks to continue, take_spectrum will be called again with override set to True
            ok = self.check_mandatory_input()  # check things that have to be right in order to continue e.g. valid number of spectra to average
            if not ok:
                return

            # now check things that are optional e.g. having reasonable sample labels, taking a white reference at every geom.
            valid_input = False
            if action == self.take_spectrum:
                valid_input = self.check_optional_input(self.take_spectrum, [True, False, garbage], range_warnings)
            elif action == self.acquire or action == self.wr:
                valid_input = self.check_optional_input(action, [True, False], range_warnings)
            elif action == self.opt:
                valid_input = self.check_optional_input(self.opt, [True, False], range_warnings)
            if not valid_input:
                return
                # Make sure RS3 save config and instrument config are taken care of. This will add those actions to the queue if needed.

        if not setup_complete:
            if action == self.take_spectrum:
                setup = self.setup_RS3_config({self.take_spectrum: [True, False, garbage]})
            elif action == self.wr or action == self.acquire:
                setup = self.setup_RS3_config({action: [True, False]})
            elif action == self.opt:
                setup = self.setup_RS3_config({self.opt: [True,
                                                          False]})  # override=True (because we just checked those things?), setup_complete=False

            else:
                raise Exception()
            # If things were not already set up (instrument config, etc) then the compy will take care of that and call take_spectrum again after it's done.
            if not setup:
                return

        if action == self.take_spectrum:
            startnum_str = str(self.spec_startnum_entry.get())
            while len(startnum_str) < NUMLEN:
                startnum_str = '0' + startnum_str
            if not garbage:
                label = ''
                if self.white_referencing:  # This will be true when we are saving the spectrum after the white reference
                    label = 'White Reference'
                else:
                    label = self.sample_label_entries[self.current_sample_gui_index].get()
                self.spec_commander.take_spectrum(self.spec_save_path, self.spec_basename, startnum_str, label,
                                                  self.science_i, self.science_e, self.science_az)
                handler = SpectrumHandler(self)
            else:
                self.spec_commander.take_spectrum(self.spec_save_path, self.spec_basename, startnum_str, 'GARBAGE',
                                                  self.science_i, self.science_e, self.science_az)
                handler = SpectrumHandler(self, title='Collecting garbage...', label='Collecting garbage spectrum...')

        elif action == self.wr:
            self.spec_commander.white_reference()
            handler = WhiteReferenceHandler(self)

        elif action == self.opt:
            self.spec_commander.optimize()
            handler = OptHandler(self)

        elif action == self.acquire:
            self.build_queue()
            self.next_in_queue()

    def build_queue(self):
        script_queue = list(
            self.queue)  # If we're running a script, the queue might have a lot of commands in it that will need to be executed after we're done acquiring. save these, we'll append them in a moment.
        self.queue = []

        # For each (i, e, az), opt, white reference, save the white reference, move the tray, take a  spectrum, then move the tray back, then update geom to next.

        for index, entry in enumerate(
                self.active_incidence_entries):  # This is one for each geometry when geometries are specified individually. When a range is specified, we actually quietly create pretend entry objects for each pair, so it works then too.
            if index == 0:
                self.queue.append({self.next_geom: [False]})  # For the first, don't complete anything
            else:
                self.queue.append({self.next_geom: []})
            self.queue.append({self.move_tray: ['wr']})
            self.queue.append({self.opt: [True, True]})
            self.queue.append({self.wr: [True, True]})
            self.queue.append({self.take_spectrum: [True, True, False]})
            for pos in self.taken_sample_positions:  # e.g. 'Sample 1'
                self.queue.append({self.move_tray: [pos]})
                self.queue.append({self.take_spectrum: [True, True, True]})  # Save and delete a garbage spectrum
                self.queue.append({self.take_spectrum: [True, True, False]})  # Save a real spectrum

        # Return tray to wr position when finished
        self.queue.append({self.move_tray: ['wr']})

        # Now append the script queue we saved at the beginning. But check if acquire is the first command in the script queue and if it is, complete that item.
        if self.script_running:
            if len(script_queue) > 0:
                while self.acquire in script_queue[0]:
                    script_queue.pop(0)
            self.queue = self.queue + script_queue

    # updates motor and science angle values, animates goniometer arms moving
    def set_and_animate_geom(self, complete_queue_item=False):
        if self.manual_automatic.get() == 1:  # automatic mode
            next_science_i = int(self.active_incidence_entries[0].get())
            next_science_e = int(self.active_emission_entries[0].get())
            next_science_az = int(self.active_azimuth_entries[0].get())

        else:  # in manual mode, it's ok if the specified geometry is invalid.
            try:
                next_science_i = int(self.incidence_entries[0].get())
            except:
                next_science_i = None

            try:
                next_science_e = int(self.emission_entries[0].get())
            except:
                next_science_e = None

            try:
                next_science_az = int(self.azimuth_entries[0].get())
            except:
                next_science_az = None

            #         if self.science_i==None or self.science_e==None or self.science_az==None:
        #             self.angles_change_time=time.time()
        if self.science_i != next_science_i or self.science_e != next_science_e or self.science_az != next_science_az:
            self.angles_change_time = time.time()

        self.science_i = next_science_i
        self.science_e = next_science_e
        self.science_az = next_science_az

        valid_i = validate_int_input(next_science_i, self.min_science_i, self.max_science_i)
        valid_e = validate_int_input(next_science_e, self.min_science_e, self.max_science_e)
        valid_az = validate_int_input(next_science_az, self.min_science_az, self.max_science_az)

        temp_queue = []
        if not (valid_i and valid_e and valid_az):
            if self.manual_automatic.get() == 1:
                raise Exception(
                    'Invalid geometry: ' + str(next_science_i) + ' ' + str(next_science_e) + ' ' + str(next_science_az))
            else:
                self.goniometer_view.invalid = True
                if valid_i:
                    self.goniometer_view.set_incidence(next_science_i)
                if valid_e:
                    self.goniometer_view.set_emission(next_science_e)
                if valid_az:
                    self.goniometer_view.set_azimuth(next_science_az)


        else:
            self.goniometer_view.invalid = False
            if self.manual_automatic.get() == 0:  # Manual mode. Might not know motor position, just use visualization position.
                current = (self.goniometer_view.motor_i, self.goniometer_view.motor_e, self.goniometer_view.motor_az)
            else:
                current = (self.motor_i, self.motor_e, self.motor_az)
            movements = self.get_movements(next_science_i, next_science_e, next_science_az, current)

            for movement in movements:
                if 'az' in movement:
                    next_motor_az = movement['az']
                    temp_queue.append({self.goniometer_view.set_azimuth: [next_motor_az]})
                elif 'e' in movement:
                    next_motor_e = movement['e']
                    temp_queue.append({self.goniometer_view.set_emission: [next_motor_e]})
                elif 'i' in movement:
                    next_motor_i = movement['i']
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

    def set_text(self, widget, text):
        state = widget.cget('state')
        widget.configure(state='normal')
        widget.delete(0, 'end')
        widget.insert(0, text)
        widget.configure(state=state)

    def safe_az_sweep(self, i, e, start_az, end_az):
        az_array = np.arange(start_az, end_az, 1)
        if len(az_array) == 0:
            az_array = np.arange(start_az, end_az, -1)
        az_array = np.append(az_array, end_az)

        for az in az_array:
            tup = (i, e, az)
            pos, dist = self.get_closest_approach(i, e, az)

            if dist < self.required_angular_separation:
                return False
        return True

    def safe_e_sweep(self, i, az, start_e, end_e):
        e_array = np.arange(start_e, end_e, 1)
        if len(e_array) == 0:
            e_array = np.arange(start_e, end_e, -1)
        e_array = np.append(e_array, end_e)

        for e in e_array:
            pos, dist = self.get_closest_approach(i, e, az)
            if dist < self.required_angular_separation:
                return False
        return True

    def safe_i_sweep(self, e, az, start_i, end_i):
        i_array = np.arange(start_i, end_i, 1)
        if len(i_array) == 0:
            i_array = np.arange(start_i, end_i, -1)
        i_array = np.append(i_array, end_i)

        for i in i_array:
            pos, dist = self.get_closest_approach(i, e, az)

            if dist < self.required_angular_separation:
                return False
        return True

    def get_movements(self, next_science_i, next_science_e, next_science_az, current_motor=None):
        movement_order = ['i', 'e', 'az']
        return movement_order

        if current_motor == None:
            current_motor = (self.motor_i, self.motor_e, self.motor_az)

        current_motor_i = int(current_motor[0])
        current_motor_e = int(current_motor[1])
        current_motor_az = int(current_motor[2])

        next_science_i = int(next_science_i)
        next_science_e = int(next_science_e)
        next_science_az = int(next_science_az)

        current_science_i, current_science_e, current_science_az = self.motor_pos_to_science_pos(current_motor_i,
                                                                                                 current_motor_e,
                                                                                                 current_motor_az)

        movement_order = None

        # Check whether the final position is valid. If not, don't search for a path, just return None.
        valid_final = self.validate_distance(next_science_i, next_science_e, next_science_az)
        if not valid_final: return None

        def convert_based_on_motor_pos(movement_order):
            if current_motor_az >= 180 and movement_order != None:
                if 'az' in movement_order:
                    movement_order[movement_order.index('az')] = 'az+180'
                    movement_order[movement_order.index('i')] = '-i'
                    if 'temp i' in movement_order:
                        movement_order[movement_order.index('temp i')] = 'reverse temp i'
                    if '-temp i' in movement_order:
                        movement_order[movement_order.index('-temp i')] = 'reverse temp i'
                elif 'az-180' in movement_order:
                    movement_order[movement_order.index('az-180')] = 'az'
                    movement_order[movement_order.index('-i')] = 'i'
                    if 'temp i' in movement_order:
                        movement_order[movement_order.index('temp i')] = 'reverse temp i'
                    if '-temp i' in movement_order:
                        movement_order[movement_order.index('-temp i')] = 'reverse temp i'
                elif 'az+180' in movement_order:
                    raise Exception('Illegal motor pos ' + str(current_motor_pos) + ' az+180')
                    pass
                    # raise(Exception('YIKES super positive!'))
            elif current_motor_az < 0 and movement_order != None:
                if 'az' in movement_order:
                    movement_order[movement_order.index('az')] = 'az-180'
                    movement_order[movement_order.index('i')] = '-i'
                    if '-temp i' in movement_order:
                        movement_order[movement_order.index('-temp i')] = 'reverse temp i'
                    if 'temp i' in movement_order:
                        movement_order[movement_order.index('temp i')] = 'reverse temp i'
                elif 'az+180' in movement_order:
                    movement_order[movement_order.index('az+180')] = 'az'
                    movement_order[movement_order.index('-i')] = 'i'
                    if '-temp i' in movement_order:
                        movement_order[movement_order.index('-temp i')] = 'reverse temp i'
                    if 'temp i' in movement_order:
                        movement_order[movement_order.index('temp i')] = 'reverse temp i'

                elif 'az-180' in movement_order:
                    #                     movement_order[movement_order.index]
                    raise Exception('Illegal motor pos')
                    pass
                    # pass
                    # raise(Exception('YIKES super negative!'))

            return movement_order

        def check_allowed_for_motors(motion_string):
            if motion_string == 'az':  # going to try a direct path to the next science az
                if current_motor_az >= 180 and next_science_az > self.max_motor_az - 180:  # 90: #takes us to a very positive motor az
                    return False
                elif current_motor_az < 0 and next_science_az < self.min_motor_az + 180:  # 90: #takes us to a very negative motor az
                    return False
                else:
                    return True

            elif motion_string == 'az-180':  # going to try turning left, passing through 0 before we reach az
                if current_motor_az < 0:
                    return False
                else:
                    next_motor_az = 0 - (180 - next_science_az)
                    if next_motor_az >= self.min_motor_az:  # -90:
                        return True
                    else:
                        return False

            elif motion_string == 'az+180':  # going to try turning right, passing through 180 before we reach az
                if current_motor_az >= 180:
                    return False
                else:
                    next_motor_az = 180 + next_science_az
                    if next_motor_az <= self.max_motor_az:  # 270:
                        return True
                    else:
                        return False
            else:
                raise Exception('how to check? ' + motion_string)

        # try moving az, i, e. If that doesn't work, try az, e, i.
        if check_allowed_for_motors(
                'az'):  # First thing to consider is whether moving straight to azimuth position would be outside motor range
            safe_az = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, next_science_az)
            if safe_az:
                safe_i = self.safe_i_sweep(current_science_e, next_science_az, current_science_i, next_science_i)
                if safe_i:
                    safe_e = self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        print('1')
                        movement_order = ['az', 'i', 'e']
                if movement_order == None:
                    safe_e = self.safe_e_sweep(current_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        safe_i = self.safe_i_sweep(next_science_e, next_science_az, current_science_i, next_science_i)
                        if safe_i:
                            print('2')
                            movement_order = ['az', 'e', 'i']

        # try moving azimuth +180, i, e. If that doesn't work, try az, e, i.
        if movement_order == None and check_allowed_for_motors('az+180'):
            safe_az1 = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 179)
            safe_az2 = self.safe_az_sweep(-1 * current_science_i, current_science_e, 0, next_science_az)
            if safe_az1 and safe_az2:

                safe_i = self.safe_i_sweep(current_science_e, next_science_az, -1 * current_science_i, next_science_i)
                if safe_i:
                    safe_e = self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        print('3')
                        movement_order = ['az+180', '-i', 'e']
                if movement_order == None:  # and next_science_az<=90:
                    safe_e = self.safe_e_sweep(-1 * current_science_i, next_science_az, current_science_e,
                                               next_science_e)
                    if safe_e:
                        safe_i = self.safe_i_sweep(next_science_e, next_science_az, -1 * current_science_i,
                                                   next_science_i)
                        if safe_i:
                            print('4')

                            movement_order = ['az+180', 'e', '-i']

        if movement_order == None and check_allowed_for_motors('az-180'):
            safe_az_1 = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 0)
            safe_az_2 = self.safe_az_sweep(-1 * current_science_i, current_science_e, 179,
                                           next_science_az)  # get_closest_approach reverses i for az<180
            if safe_az_1 and safe_az_2:
                safe_i = self.safe_i_sweep(current_science_e, next_science_az, -1 * current_science_i, next_science_i)
                if safe_i:
                    safe_e = self.safe_e_sweep(next_science_i, next_science_az, current_science_e, next_science_e)
                    if safe_e:
                        print('5')
                        movement_order = ['az-180', '-i', 'e']
                if movement_order == None:
                    safe_e = self.safe_e_sweep(-1 * current_science_i, next_science_az, current_science_e,
                                               next_science_e)
                    if safe_e:
                        safe_i = self.safe_i_sweep(next_science_e, next_science_az, -1 * current_science_i,
                                                   next_science_i)
                        if safe_i:
                            print('6')
                            movement_order = ['az-180', 'e', '-i']

        # Try a temporary i position
        if movement_order == None:
            if current_science_e >= 0:
                temp_i = -1 * (current_science_e + 2 * self.required_angular_separation)
            else:
                temp_i = -1 * (current_science_e - 2 * self.required_angular_separation)
            temp_i_str = 'temp i'

            safe_temp_i = self.safe_i_sweep(current_science_e, current_science_az, current_science_i, temp_i)
            if not safe_temp_i:
                temp_i_str = '-temp i'
                temp_i = -1 * temp_i
                safe_temp_i = self.safe_i_sweep(current_science_e, current_science_az, current_science_i, temp_i)

            if safe_temp_i:
                if check_allowed_for_motors('az'):
                    # try moving az, i, e
                    safe_az = self.safe_az_sweep(temp_i, current_science_e, current_science_az, next_science_az)
                    if safe_az:
                        safe_i = self.safe_i_sweep(current_science_e, next_science_az, temp_i, next_science_i)
                        if safe_i:
                            safe_e = self.safe_e_sweep(next_science_i, next_science_az, current_science_e,
                                                       next_science_e)
                            if safe_e:
                                print('7')
                                movement_order = [temp_i_str, 'az', 'i', 'e']
                        else:
                            safe_e = self.safe_e_sweep(temp_i, next_science_az, current_science_e, next_science_e)
                            if safe_e:
                                safe_i = self.safe_i_sweep(next_science_e, next_science_az, temp_i, next_science_i)
                                if safe_i:
                                    print('8')
                                    movement_order = [temp_i_str, 'az', 'e', 'i']

                if movement_order == None and check_allowed_for_motors('az+180'):
                    # try moving azimuth +180, i, e. If that doesn't work, try az+180, e, i.
                    safe_az1 = self.safe_az_sweep(temp_i, current_science_e, current_science_az, 179)
                    safe_az2 = self.safe_az_sweep(-1 * temp_i, current_science_e, 0, next_science_az)
                    if safe_az1 and safe_az2:
                        safe_i = self.safe_i_sweep(current_science_e, next_science_az, -1 * temp_i, next_science_i)
                        if safe_i:
                            safe_e = self.safe_e_sweep(next_science_i, next_science_az, current_science_e,
                                                       next_science_e)
                            if safe_e:
                                print('9')
                                movement_order = [temp_i_str, 'az+180', '-i', 'e']
                        if movement_order == None:
                            safe_e = self.safe_e_sweep(-1 * temp_i, next_science_az, current_science_e, next_science_e)
                            if safe_e:
                                safe_i = self.safe_i_sweep(next_science_e, next_science_az, -1 * temp_i, next_science_i)
                                if safe_i:
                                    print('10')
                                    movement_order = [temp_i_str, 'az+180', 'e', '-i']

                if movement_order == None and check_allowed_for_motors('az-180'):
                    safe_az1 = self.safe_az_sweep(temp_i, current_science_e, current_science_az, 0)
                    safe_az2 = self.safe_az_sweep(-1 * temp_i, current_science_e, 179, next_science_az)
                    if safe_az1 and safe_az2:
                        safe_i = self.safe_i_sweep(current_science_e, next_science_az, -1 * temp_i, next_science_i)
                        if safe_i:
                            safe_e = self.safe_e_sweep(next_science_i, next_science_az, current_science_e,
                                                       next_science_e)
                            if safe_e:
                                print('11')
                                movement_order = [temp_i_str, 'az-180', '-i', 'e']
                        if movement_order == None:
                            safe_e = self.safe_e_sweep(-1 * temp_i, next_science_az, current_science_e, next_science_e)
                            if safe_e:
                                safe_i = self.safe_i_sweep(next_science_e, next_science_az, -1 * temp_i, next_science_i)
                                if safe_i:
                                    print('12')
                                    movement_order = [temp_i_str, 'az-180', 'e', '-i']

        if movement_order == None:
            # Try movning to az 90, temp i at 40, move e, move i
            i_negative = False
            if current_motor_az >= 0 and current_motor_az < 180:
                safe_temp_az = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 90)

            elif current_motor_az < 0:
                safe_temp_az_1 = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 179)
                safe_temp_az_2 = self.safe_az_sweep(-1 * current_science_i, current_science_e, 0, 90)
                safe_temp_az = safe_temp_az_1 and safe_temp_az_2
                i_negative = True
            elif current_motor_az >= 180:
                safe_temp_az_1 = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 0)
                safe_temp_az_2 = self.safe_az_sweep(-1 * current_science_i, current_science_e, 179, 90)
                safe_temp_az = safe_temp_az_1 and safe_temp_az_2
                i_negative = True
            if safe_temp_az:
                if i_negative:
                    safe_temp_i = self.safe_i_sweep(current_science_e, 90, -1 * current_science_i, 40)
                else:
                    safe_temp_i = self.safe_i_sweep(current_science_e, 90, current_science_i, 40)
                if safe_temp_i:
                    safe_e = self.safe_e_sweep(40, 90, current_science_e, next_science_e)
                    if safe_e:
                        safe_i = self.safe_i_sweep(next_science_e, 90, 40, next_science_i)
                        if safe_i:
                            safe_az = self.safe_az_sweep(next_science_i, next_science_e, 90, next_science_az)
                            if safe_az:
                                print('13')
                                movement_order = ['az 90', 'i 40', 'e', 'i', 'az']
                        if movement_order == None and next_science_az >= self.min_motor_az + 180:  # 90:
                            safe_i = self.safe_i_sweep(next_science_e, 90, 40, -1 * next_science_i)
                            if safe_i:
                                safe_az_1 = self.safe_az_sweep(-1 * next_science_i, next_science_e, 90, 0)
                                safe_az_2 = self.safe_az_sweep(next_science_i, next_science_e, 179, next_science_az)
                                if safe_az_1 and safe_az_2:
                                    print('14')
                                    movement_order = ['az 90', 'i 40', 'e', '-i', 'az-180']
                        if movement_order == None and next_science_az <= self.max_motor_az - 180:  # 90:
                            safe_i = self.safe_i_sweep(next_science_e, 90, 40, -1 * next_science_i)
                            if safe_i:
                                safe_az_1 = self.safe_az_sweep(-1 * next_science_i, next_science_e, 90, 179)
                                safe_az_2 = self.safe_az_sweep(next_science_i, next_science_e, 0, next_science_az)
                                if safe_az_1 and safe_az_2:
                                    print('15')
                                    movement_order = ['az 90', 'i 40', 'e', '-i', 'az+180']

        #         if movement_order==None:
        #             #Try movning to temp i at 40, az 90, move e, move i, move az
        #             if current_motor_az>=0 and current_motor_az<180:
        #                 safe_temp_i=self.safe_i_sweep(current_science_e, current_science_az, current_science_i, 40)
        #                 temp_i_str='i 40'
        #             elif current_motor_az<0:
        #                 safe_temp_i=self.safe_i_sweep(current_science_e, current_science_az, current_science_i, -40)
        #                 temp_i_str='i -40'
        #             elif current_motor_az>=180:
        #                 safe_temp_i=self.safe_i_sweep(current_science_e, current_science_az, current_science_i, -40)
        #                 temp_i_str='i -40'
        #
        #             if safe_temp_i:
        #                 if current_motor_az>=0 and current_motor_az<180:
        #                     safe_temp_az=self.safe_az_sweep(40, current_science_e, current_science_az, 90)
        #                 elif current_motor_az<0:
        #                     safe_temp_az_1=self.safe_az_sweep(-40, current_science_e, current_science_az, 179)
        #                     safe_temp_az_2=self.safe_az_sweep(40, current_science_e,0,90)
        #                     safe_temp_az=safe_temp_az_1 and safe_temp_az_2
        #                 elif current_motor_az>=180:
        #                     safe_temp_az_1=self.safe_az_sweep(-40, current_science_e, current_science_az, 0)
        #                     safe_temp_az_2=self.safe_az_sweep(40, current_science_e, 179, 90)
        #                     safe_temp_az=safe_temp_az_1 and safe_temp_az_2
        #
        #                 if safe_temp_az:
        #                     safe_e=self.safe_e_sweep(40,90,current_science_e, next_science_e)
        #                     if safe_e:
        #                         safe_i=self.safe_i_sweep(next_science_e, 90, 40, next_science_i)
        #                         if safe_i:
        #                             safe_az=self.safe_az_sweep(next_science_i, next_science_e, 90, next_science_az)
        #                             if safe_az:
        #                                 print('24')
        #                                 movement_order=[temp_i_str,'az 90','e','i','az']
        #                         if movement_order==None and next_science_az>=90:
        #                             safe_i=self.safe_i_sweep(next_science_e, 90,40, -1*next_science_i)
        #                             if safe_i:
        #                                 safe_az_1=self.safe_az_sweep(-1*next_science_i, next_science_e, 90,0)
        #                                 safe_az_2=self.safe_az_sweep(next_science_i, next_science_e, 179,next_science_az)
        #                                 if safe_az_1 and safe_az_2:
        #                                     print('25')
        #                                     movement_order=[temp_i_str,'az 90','e','-i','az-180']
        #                         if movement_order==None and next_science_az<=90:
        #                             safe_i=self.safe_i_sweep(next_science_e, 90,40, -1*next_science_i)
        #                             if safe_i:
        #                                 safe_az_1=self.safe_az_sweep(-1*next_science_i, next_science_e, 90,179)
        #                                 safe_az_2=self.safe_az_sweep(next_science_i, next_science_e, 0,next_science_az)
        #                                 if safe_az_1 and safe_az_2:
        #                                     print('26')
        #                                     movement_order=[temp_i_str,'az 90','e','-i','az+180']

        if movement_order == None and current_motor_az >= 90:
            # Try movning motor az to 270, temp i at 40, move e, move i
            i_negative = False
            if current_motor_az >= 0 and current_motor_az < 180:
                safe_temp_az_1 = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 179)
                safe_temp_az_2 = self.safe_az_sweep(-1 * current_science_i, current_science_e, 0, 90)
                safe_temp_az = safe_temp_az_1 and safe_temp_az_2
                i_negative = True

            elif current_motor_az > 180:
                safe_temp_az = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 90)
            else:  # Never reach here, motor_az always >90
                safe_temp_az_1 = self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 179)
                safe_temp_az_2 = self.safe_az_sweep(-1 * current_science_i, current_science_e, 0, 179)
                safe_temp_az_3 = self.safe_az_sweep(current_science_i, current_science_e, 0, 90)
                safe_az = safe_temp_az_1 and safe_temp_az_2 and safe_temp_az_3

            if safe_temp_az:
                if i_negative:
                    safe_temp_i = self.safe_i_sweep(current_science_e, 90, -1 * current_science_i, 40)
                else:
                    safe_temp_i = self.safe_i_sweep(current_science_e, 90, current_science_i, 40)
                if safe_temp_i:
                    safe_e = self.safe_e_sweep(20, 90, current_science_e, next_science_e)
                    if safe_e:
                        safe_i = self.safe_i_sweep(next_science_e, 90, 40, -1 * next_science_i)
                        if safe_i and next_science_az <= 90:
                            safe_az = self.safe_az_sweep(next_science_i, next_science_e, 90, next_science_az)
                            if safe_az:
                                print('16')
                                movement_order = ['az 270', 'i -40', 'e', '-i', 'az+180']

                        if movement_order == None:
                            safe_i = self.safe_i_sweep(next_science_e, 90, 40, -1 * next_science_i)
                            if safe_i:
                                safe_az_1 = self.safe_az_sweep(-1 * next_science_i, next_science_e, 90, 0)
                                safe_az_2 = self.safe_az_sweep(next_science_i, next_science_e, 179, next_science_az)
                                safe_az = safe_az_1 and safe_az_2
                                if safe_az:
                                    print('17')
                                    movement_order = ['az 270', 'i -40', 'e', 'i', 'az']

        #         if movement_order==None and current_motor_az<180:
        #             #Try movning to az -90, temp i at 20, move e, move i
        #             i_negative=False
        #             if current_motor_az>=0 and current_motor_az<180:
        #                 safe_temp_az_1=self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 0)
        #                 safe_temp_az_2=self.safe_az_sweep(-1*current_science_i, current_science_e, 179,90)
        #                 safe_temp_az=safe_temp_az_1 and safe_temp_az_2
        #                 i_negative=True
        #
        #             elif current_motor_az<0:
        #                 safe_temp_az=self.safe_az_sweep(current_science_i, current_science_e, current_science_az, 90)
        #
        #             if safe_temp_az:
        #                 print('MOTOR AZ -90')
        #                 if i_negative:
        #                     safe_temp_i=self.safe_i_sweep(current_science_e, 90,-1*current_science_i,20)
        #                 else:
        #                     safe_temp_i=self.safe_i_sweep(current_science_e, 90,current_science_i,20)
        #                 if safe_temp_i:
        #                     safe_e=self.safe_e_sweep(20,90,current_science_e, next_science_e)
        #                     if safe_e:
        #                         safe_i=self.safe_i_sweep(next_science_e, 90,20, next_science_i)
        #                         if safe_i and next_science_az>=90:
        #                             safe_az_1=self.safe_az_sweep(next_science_i, next_science_e, 90,next_science_az)
        #                             if safe_az_1 and safe_az_2:
        #                                 print('19')
        #                                 movement_order=['az 90','i 20','e','i','az-180']
        #
        #                         if movement_order==None:
        #                             safe_i=self.safe_i_sweep(next_science_e, 90, 20, -1*next_science_i)
        #                             if safe_i:
        #                                 safe_az_1=self.safe_az_sweep(-1*next_science_i, next_science_e, 90, 179)
        #                                 safe_az_2=self.safe_az_sweep(next_science_i,0,next_science_az )
        #                                 safe_az=safe_az_1 and safe_az_2
        #                                 if safe_az:
        #                                     print('20')
        #                                     movement_order=['az 90','i 20','e','-i','az']

        if movement_order == None:
            #                   1. setting temp e to out of the way (i+20)
            #                   2. rotating az to 90
            #                   3. set i to abs(e)+20
            #                   3. set e
            #                   4. set az, i to -i
            #                   5. set i
            temp_e_str = 'temp e'

            temp_e = np.abs(current_science_i) + 2 * self.required_angular_separation
            if current_science_e < current_science_i and current_science_az < 90:
                temp_e = -1 * temp_e
            elif current_science_e > current_science_i and current_science_az > 90:
                temp_e = -1 * temp_e

            safe_temp_e = self.safe_e_sweep(current_science_i, current_science_az, current_science_e, temp_e)

            if not safe_temp_e:
                temp_e_str = '-temp e'
                temp_e = -1 * temp_e
                safe_temp_e = self.safe_e_sweep(current_science_i, current_science_az, current_science_e, temp_e)

            if safe_temp_e:
                i_negative = False
                if current_motor_az >= 0 and current_motor_az < 180:
                    safe_temp_az = self.safe_az_sweep(current_science_i, temp_e, current_science_az, 90)

                elif current_motor_az < 0:
                    safe_temp_az_1 = self.safe_az_sweep(current_science_i, temp_e, current_science_az, 179)
                    safe_temp_az_2 = self.safe_az_sweep(-1 * current_science_i, temp_e, 0, 90)
                    safe_temp_az = safe_temp_az_1 and safe_temp_az_2
                    i_negative = True
                elif current_motor_az >= 180:
                    safe_temp_az_1 = self.safe_az_sweep(current_science_i, temp_e, current_science_az, 0)
                    safe_temp_az_2 = self.safe_az_sweep(-1 * current_science_i, temp_e, 179, 90)
                    safe_temp_az = safe_temp_az_1 and safe_temp_az_2
                    i_negative = True
                if safe_temp_az:
                    temp_i_pos = np.abs(next_science_e) + 2 * self.required_angular_separation
                    if i_negative:
                        safe_temp_i = self.safe_i_sweep(temp_e, 90, -1 * current_science_i, temp_i_pos)
                    else:
                        safe_temp_i = self.safe_i_sweep(temp_e, 90, current_science_i, temp_i_pos)
                    if safe_temp_i:
                        safe_e = self.safe_e_sweep(temp_i_pos, 90, temp_e, next_science_e)
                        if safe_e:
                            safe_az = self.safe_az_sweep(temp_i_pos, next_science_e, 90, next_science_az)
                            if safe_az:
                                safe_i = self.safe_i_sweep(next_science_e, next_science_az, temp_i_pos, next_science_i)
                                if safe_i:
                                    print('18')
                                    movement_order = [temp_e_str, 'az 90', 'temp i pos', 'e', 'az', 'i']

                            if movement_order == None and next_science_az <= 90:
                                safe_az_1 = self.safe_az_sweep(temp_i_pos, next_science_e, 90, 179)
                                safe_az_2 = self.safe_az_sweep(-1 * temp_i_pos, next_science_e, 0, next_science_az)
                                if safe_az_1 and safe_az_2:
                                    safe_i = self.safe_i_sweep(next_science_e, next_science_az, -1 * temp_i_pos,
                                                               next_science_i)
                                    if safe_i:
                                        print('19')
                                        movement_order = [temp_e_str, 'az 90', 'temp i pos', 'e', 'az+180', '-i']
                                if movement_order == None:
                                    safe_i = self.safe_i_sweep(next_science_e, next_science_az, temp_i_pos,
                                                               -1 * next_science_i)
                                    if safe_i:
                                        safe_az_1 = self.safe_az_sweep(-1 * next_science_i, next_science_e, 90, 179)
                                        safe_az_2 = self.safe_az_sweep(next_science_i, next_science_e, 0,
                                                                       next_science_az)
                                        if safe_az_1 and safe_az_2:
                                            print('20')
                                            movement_order = [temp_e_str, 'az 90', 'temp i pos', 'e', '-i', 'az+180']

                            if movement_order == None and next_science_az >= 90:
                                safe_az_1 = self.safe_az_sweep(temp_i_pos, next_science_e, 90, 0)
                                safe_az_2 = self.safe_az_sweep(-1 * temp_i_pos, next_science_e, 179, next_science_az)
                                if safe_az_1 and safe_az_2:
                                    safe_i = self.safe_i_sweep(next_science_e, next_science_az, -1 * temp_i_pos,
                                                               next_science_i)
                                    if safe_i:
                                        print('21')
                                        movement_order = [temp_e_str, 'az 90', 'temp i pos', 'e', 'az-180', '-i']
                                if movement_order == None:
                                    safe_i = self.safe_i_sweep(next_science_e, next_science_az, temp_i_pos,
                                                               -1 * next_science_i)
                                    if safe_i:
                                        safe_az_1 = self.safe_az_sweep(-1 * next_science_i, next_science_e, 90, 0)
                                        safe_az_2 = self.safe_az_sweep(next_science_i, next_science_e, 179,
                                                                       next_science_az)
                                        if safe_az_1 and safe_az_2:
                                            print('22')
                                            movement_order = [temp_e_str, 'az 90', 'temp i pos', 'e', '-i', 'az-180']

                            if movement_order == None:
                                safe_az = self.safe_az_sweep(temp_i_pos, next_science_e, 90, next_science_az)
                                if safe_az:
                                    safe_i = self.safe_i_sweep(next_science_e, next_science_az, temp_i_pos,
                                                               next_science_i)
                                    if safe_i:
                                        print('23')
                                        movement_order = ['temp e', 'az 90', 'temp i pos', 'e', 'az', 'i']

        if movement_order != None:
            if 'temp e' not in movement_order and '-temp e' not in movement_order and 'az 90' not in movement_order and 'az 270' not in movement_order:
                movement_order = convert_based_on_motor_pos(movement_order)

            movements = []
            for movement in movement_order:
                if movement == 'az':
                    movements.append({'az': next_science_az})
                elif movement == 'az+180':
                    movements.append({'az': next_science_az + 180})
                elif movement == 'az-180':
                    movements.append({'az': next_science_az - 180})
                elif movement == 'az 90':
                    movements.append({'az': 90})
                elif movement == 'az 270':
                    movements.append({'az': 270})
                elif 'temp e' == movement:
                    movements.append({'e': temp_e})
                elif '-temp e' == movement:
                    movements.append({'e': temp_e})
                elif 'temp i' == movement:
                    movements.append({'i': temp_i})
                elif '-temp i' == movement:
                    movements.append({'i': temp_i})
                elif 'temp i pos' == movement:
                    movements.append({'i': temp_i_pos})
                elif 'i 20' == movement:
                    movements.append({'i': 20})
                elif 'i -20' == movement:
                    movements.append({'i': -20})
                elif 'i 40' == movement:
                    movements.append({'i': 40})
                elif 'i -40' == movement:
                    movements.append({'i': -40})
                elif movement == 'i':
                    movements.append({'i': next_science_i})
                elif movement == '-i':
                    movements.append({'i': -1 * next_science_i})
                elif movement == 'e':
                    movements.append({'e': next_science_e})
                elif movement == 'reverse temp i':
                    movements.append({'i': -1 * temp_i})
                else:
                    print('MISING MOVEMENT: ' + movement)
        else:
            movements = None

        return movements

    def next_geom(self, complete_last=True):
        self.complete_queue_item()
        if complete_last:
            self.active_incidence_entries.pop(0)
            self.active_emission_entries.pop(0)
            self.active_azimuth_entries.pop(0)
            if self.individual_range.get() == 0:
                self.active_geometry_frames.pop(0)

        next_i = int(self.active_incidence_entries[0].get())
        next_e = int(self.active_emission_entries[0].get())
        next_az = int(self.active_azimuth_entries[0].get())

        # Update goniometer position. Don't run the arms into each other
        movements = self.get_movements(next_i, next_e, next_az)

        temp_queue = []
        if movements != None:
            for movement in movements:
                if 'az' in movement:
                    next_motor_az = movement['az']
                    temp_queue.append({self.set_azimuth: [next_motor_az]})
                elif 'e' in movement:
                    next_motor_e = movement['e']
                    temp_queue.append({self.set_emission: [next_motor_e]})
                elif 'i' in movement:
                    next_motor_i = movement['i']
                    temp_queue.append({self.set_incidence: [next_motor_i]})
                else:
                    print('UNEXPECTED: ' + str(movement))
        else:
            raise Exception(
                'Error: could not find path to next geometry: ' + str(next_i) + ' ' + str(next_e) + ' ' + str(next_az))

        self.queue = temp_queue + self.queue

        self.next_in_queue()

    # def set_motion_order(self, next_i, next_e, next_az):

    # Move light will either read i from the GUI (default, i=None), or if this is a text command then i will be passed as a parameter.
    # When from the commandline, i may not be an incidence angle at all but a number of steps to move. In this case, type will be 'steps'.
    def set_incidence(self, next_motor_i=None, type='angle', negative=False):
        steps = True
        timeout = 0
        next_motor_i = int(next_motor_i)

        if type == 'angle':
            steps = False  # We will need to tell the motionhandler whether we're specifying steps or an angle

            # First check whether we actually need to move at all.
            if next_motor_i == None:
                next_science_i = int(self.active_incidence_entries[0].get())
                if self.motor_az >= 180 or self.motor_az < 0:
                    next_motor_i = -1 * next_science_i
                else:
                    next_motor_i = next_science_i
                raise Exception('No protection against unsafe incidence movement')

            if next_motor_i == self.motor_i:  # No change in incidence angle, no need to move
                self.log('Goniometer remaining at an incidence angle of ' + str(self.science_i) + ' degrees.')
                self.complete_queue_item()
                if len(self.queue) > 0:
                    self.next_in_queue()
                return  # If we're staying in the same spot, just return!
            timeout = np.abs(next_motor_i - self.motor_i) * 8 + PI_BUFFER
        else:
            timeout = np.abs(next_motor_i) / 15 + PI_BUFFER

        self.pi_commander.set_incidence(next_motor_i, type)
        handler = MotionHandler(self, label='Setting incidence...', timeout=timeout, steps=steps,
                                destination=next_motor_i)

        if type == 'angle':  # Only change the visualization if an angle is specified. Specifiying steps is for setting up the
            self.goniometer_view.set_incidence(next_motor_i)

    def set_emission(self, next_motor_e=None, type='angle'):
        steps = True
        timeout = 0
        next_motor_e = int(next_motor_e)

        if type == 'angle':
            steps = False  # We will need to tell the motionhandler whether we're specifying steps or an angle

            if next_motor_e == None:
                next_motor_e = int(
                    self.active_emission_entries[0].get())  # for emission, motor e and science e are the same.
                raise Exception('No protection against unsafe emission movement')

            # First check whether we actually need to move at all.
            if next_motor_e == self.motor_e:  # No change in incidence angle, no need to move
                self.log('Goniometer remaining at an emission angle of ' + str(self.science_e) + ' degrees.')
                self.complete_queue_item()
                if len(self.queue) > 0:
                    self.next_in_queue()
                return  # If we're staying in the same spot, just return!
            timeout = np.abs(int(next_motor_e) - int(self.motor_e)) * 8 + PI_BUFFER
        else:
            timeout = np.abs(int(next_motor_e)) / 15 + PI_BUFFER

        self.pi_commander.set_emission(next_motor_e, type)
        handler = MotionHandler(self, label='Setting emission...', timeout=timeout, steps=steps,
                                destination=next_motor_e)

        if type == 'angle':  # Only change the visualization if an angle is specified. Specifiying steps is for setting up the
            self.goniometer_view.set_emission(int(next_motor_e))

    def set_azimuth(self, next_motor_az=None, type='angle'):
        steps = True
        timeout = 0
        next_motor_az = int(next_motor_az)

        if type == 'angle':
            steps = False  # We will need to tell the motionhandler whether we're specifying steps or an angle

            if next_motor_az == None:
                next_motor_az = int(
                    self.active_azimuth_entries[0].get())  # no protection against running arms into each other.
                raise Exception('No protection against unsafe azimuth movement')

            # First check whether we actually need to move at all.
            if next_motor_az == self.motor_az:  # No change in incidence angle, no need to move
                self.log('Goniometer remaining at an azimuth angle of ' + str(self.science_az) + ' degrees.')
                self.complete_queue_item()
                if len(self.queue) > 0:
                    self.next_in_queue()
                return  # If we're staying in the same spot, just return!
            timeout = np.abs(next_motor_az - self.motor_az) * 8 + PI_BUFFER
        else:
            timeout = np.abs(next_motor_az) / 15 + PI_BUFFER

        self.pi_commander.set_azimuth(next_motor_az, type)
        handler = MotionHandler(self, label='Setting azimuth...', timeout=timeout, steps=steps,
                                destination=next_motor_az)

        if type == 'angle':  # Only change the visualization if an angle is specified. Specifiying steps is for setting up the
            self.goniometer_view.set_azimuth(next_motor_az)

    def move_tray(self, pos, type='position'):
        steps = False
        if type == 'steps': steps = True
        if type == 'position':
            self.goniometer_view.set_current_sample(pos)
        self.pi_commander.move_tray(pos, type)
        handler = MotionHandler(self, label='Moving sample tray...', timeout=30 + BUFFER, new_sample_loc=pos,
                                steps=steps)

    def range_setup(self, override=False):
        self.active_incidence_entries = []
        self.active_emission_entries = []
        self.active_azimuth_entries = []

        incidence_err_str = ''
        incidence_warn_str = ''

        first_i = self.light_start_entry.get()
        valid = validate_int_input(first_i, self.min_science_i, self.max_science_i)
        if not valid:
            incidence_err_str = 'Incidence must be a number from ' + str(self.min_science_i) + ' to ' + str(
                self.max_science_i) + '.\n'
        else:
            first_i = int(first_i)

        final_i = self.light_end_entry.get()
        valid = validate_int_input(final_i, self.min_science_i, self.max_science_i)

        if not valid:
            incidence_err_str = 'Incidence must be a number from ' + str(self.min_science_i) + ' to ' + str(
                self.max_science_i) + '.\n'
        else:
            final_i = int(final_i)

        i_interval = self.light_increment_entry.get()
        valid = validate_int_input(i_interval, 0, 2 * self.max_science_i)
        if not valid:
            incidence_err_str += 'Incidence interval must be a number from 0 to ' + str(2 * self.max_science_i) + '.\n'
        else:
            i_interval = int(i_interval)
        incidences = []
        if incidence_err_str == '':
            if i_interval == 0:
                if first_i == final_i:
                    incidences = [first_i]
                else:
                    incidences = [first_i, final_i]
                    incidence_warn_str = 'Incidence interval = 0. Using first and last given incidence values.\n'
            elif final_i > first_i:
                incidences = np.arange(first_i, final_i, i_interval)
                incidences = list(incidences)
                incidences.append(final_i)
            else:
                incidences = np.arange(first_i, final_i, -1 * i_interval)
                incidences = list(incidences)
                incidences.append(final_i)

        emission_err_str = ''
        emission_warn_str = ''

        first_e = self.detector_start_entry.get()
        valid = validate_int_input(first_e, self.min_science_e, self.max_science_e)
        if not valid:
            emission_err_str = 'Emission must be a number from ' + str(self.min_science_e) + ' to ' + str(
                self.max_science_e) + '.\n'
        else:
            first_e = int(first_e)
        final_e = self.detector_end_entry.get()
        valid = validate_int_input(final_e, self.min_science_e, self.max_science_e)

        if not valid:
            emission_err_str = 'Emission must be a number from ' + str(self.min_science_e) + ' to ' + str(
                self.max_science_e) + '.\n'
        else:
            final_e = int(final_e)

        e_interval = self.detector_increment_entry.get()
        valid = validate_int_input(e_interval, 0, 2 * self.max_science_e)
        if not valid:
            emission_err_str += 'Emission interval must be a number from 0 to ' + str(2 * self.max_science_e) + '.\n'
        else:
            e_interval = int(e_interval)
        emissions = []
        if emission_err_str == '':
            if e_interval == 0:
                if first_e == final_e:
                    emissions = [first_e]
                else:
                    emissions = [first_e, final_e]
                    emission_warn_str = 'Emission interval = 0. Using first and last given emission values.'
            elif final_e > first_e:
                emissions = np.arange(first_e, final_e, e_interval)
                emissions = list(emissions)
                emissions.append(final_e)
            else:
                emissions = np.arange(first_e, final_e, -1 * e_interval)
                emissions = list(emissions)
                emissions.append(final_e)

        err_str = 'Error: ' + incidence_err_str + emission_err_str
        if err_str != 'Error: ':
            dialog = ErrorDialog(self, title='Error', label=err_str)
            return False
        warning_string = incidence_warn_str + emission_warn_str

        azimuth_err_str = ''
        azimuth_warn_str = ''

        first_az = self.azimuth_start_entry.get()
        valid = validate_int_input(first_az, self.min_science_az, self.max_science_az)
        if not valid:
            azimuth_err_str = 'Azimuth must be a number from ' + str(self.min_science_az) + ' to ' + str(
                self.max_science_az) + '.\n'
        else:
            first_az = int(first_az)
        final_az = self.azimuth_end_entry.get()
        valid = validate_int_input(final_az, self.min_science_az, self.max_science_az)

        if not valid:
            azimuth_err_str = 'Azimuth must be a number from ' + str(self.min_science_az) + ' to ' + str(
                self.max_science_az) + '.\n'
        else:
            final_az = int(final_az)

        az_interval = self.azimuth_increment_entry.get()
        valid = validate_int_input(az_interval, 0, 2 * self.max_science_az)
        if not valid:
            azimuth_err_str += 'Azimuth interval must be a number from 0 to ' + str(2 * self.max_science_az) + '.\n'
        else:
            az_interval = int(az_interval)
        azimuths = []
        if azimuth_err_str == '':
            if az_interval == 0:
                if first_az == final_az:
                    azimuths = [first_az]
                else:
                    azimuths = [first_az, final_az]
                    azimuth_warn_str = 'Azimuth interval = 0. Using first and last given azimuth values.'
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
                    if self.validate_distance(i, e, az):
                        i_entry = PrivateEntry(str(i))
                        e_entry = PrivateEntry(str(e))
                        az_entry = PrivateEntry(str(az))
                        self.active_incidence_entries.append(i_entry)
                        self.active_emission_entries.append(e_entry)
                        self.active_azimuth_entries.append(az_entry)

        if warning_string == '':
            return True
        else:
            return warning_string

    # called when user clicks optimize button. No different than opt() except we clear out the queue first just in case there is something leftover hanging out in there.
    def opt_button_cmd(self):
        self.queue = []
        self.queue.append({self.opt: [True,
                                      True]})  # Setting override and setup_complete to True make is so if we automatically retry because of an error on the spec compy we won't have to do setup things agian.
        self.acquire(override=False, setup_complete=False, action=self.opt)

    # called when user clicks wr button. No different than wr() except we clear out the queue first just in case there is something leftover hanging out in there.
    def wr_button_cmd(self):
        self.queue = []
        self.queue.append({self.wr: [True,
                                     True]})  # Setting override and setup_complete to True make is so if we automatically retry because of an error on the spec compy we won't have to do setup things agian.
        self.queue.append({self.take_spectrum: [True, True, False]})
        self.acquire(override=False, setup_complete=False, action=self.wr)

    # called when user clicks take spectrum button. No different than take_spectrum() except we clear out the queue first just in case there is something leftover hanging out in there.
    def spec_button_cmd(self):
        self.queue = []
        self.queue.append({self.take_spectrum: [False, False,
                                                False]})  # We don't automatically retry taking spectra so there is no need to have override and setup complete set to true here as for the other two above.
        self.acquire(override=False, setup_complete=False, action=self.take_spectrum, garbage=False)

    # commands that are put in the queue for optimizing, wr, taking a spectrum.
    def opt(self, override=False, setup_complete=False):
        self.acquire(override=override, setup_complete=setup_complete, action=self.opt)

    def wr(self, override=False, setup_complete=False):
        self.acquire(override=override, setup_complete=setup_complete, action=self.wr)

    def take_spectrum(self, override, setup_complete, garbage):
        self.acquire(override=override, setup_complete=setup_complete, action=self.take_spectrum, garbage=garbage)

    def check_connection(self):
        self.connection_checker.check_connection()

    def configure_instrument(self):
        self.spec_commander.configure_instrument(self.instrument_config_entry.get())
        handler = InstrumentConfigHandler(self)

    # Set thes ave configuration for raw spectral data. First, use a remotedirectoryworker to check whether the directory exists and is writeable. If it doesn't exist, give an option to create the directory.
    def set_save_config(self):

        # This function gets called if the directory doesn't exist and the user clicks 'yes' for making the directory.
        def inner_mkdir(dir):
            status = self.remote_directory_worker.mkdir(dir)
            if status == 'mkdirsuccess':
                self.set_save_config()
            elif status == 'mkdirfailedfileexists':
                dialog = ErrorDialog(self, title='Error',
                                     label='Could not create directory:\n\n' + dir + '\n\nFile exists.')
            elif status == 'mkdirfailed':
                dialog = ErrorDialog(self, title='Error', label='Could not create directory:\n\n' + dir)

        status = self.remote_directory_worker.get_dirs(self.spec_save_dir_entry.get())

        if status == 'listdirfailed':

            if self.script_running:  # If a script is running, automatically try to make the directory.
                inner_mkdir(self.spec_save_dir_entry.get())
            else:  # Otherwise, ask the user first.
                buttons = {
                    'yes': {
                        inner_mkdir: [self.spec_save_dir_entry.get()]
                    },
                    'no': {
                        self.reset: []
                    }
                }
                dialog = ErrorDialog(self, title='Directory does not exist',
                                     label=self.spec_save_dir_entry.get() + '\n\ndoes not exist. Do you want to create this directory?',
                                     buttons=buttons)
            return

        elif status == 'listdirfailedpermission':
            dialog = ErrorDialog(self, label='Error: Permission denied for\n' + self.spec_save_dir_entry.get())
            return

        elif status == 'timeout':
            if not self.text_only:
                buttons = {
                    'cancel': {},
                    'retry': {self.spec_commander.remove_from_listener_queue: [['timeout']], self.next_in_queue: []}
                }
                try:  # Do this if there is a wait dialog up
                    self.wait_dialog.interrupt(
                        'Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer\n computer and the spectrometer is connected.')
                    self.wait_dialog.set_buttons(buttons)  # , buttons=buttons)
                    self.wait_dialog.top.geometry('376x175')
                    for button in self.wait_dialog.tk_buttons:
                        button.config(width=15)
                except:
                    dialog = ErrorDialog(self,
                                         label='Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer\n computer and the spectrometer is connected.',
                                         buttons=buttons)
                    dialog.top.geometry('376x145')
                    for button in dialog.tk_buttons:
                        button.config(width=15)
            else:
                self.log('Error: Operation timed out while trying to set save configuration')
            return
        self.spec_commander.check_writeable(self.spec_save_dir_entry.get())
        t = 3 * BUFFER
        while t > 0:
            if 'yeswriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('yeswriteable')
                break
            elif 'notwriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('notwriteable')
                dialog = ErrorDialog(self, label='Error: Permission denied.\nCannot write to specified directory.')
                return
            time.sleep(INTERVAL)
            t = t - INTERVAL
        if t <= 0:
            dialog = ErrorDialog(self, label='Error: Operation timed out.')
            return

        spec_num = self.spec_startnum_entry.get()
        while len(spec_num) < NUMLEN:
            spec_num = '0' + spec_num

        self.spec_commander.set_save_path(self.spec_save_dir_entry.get(), self.spec_basename_entry.get(),
                                          self.spec_startnum_entry.get())
        handler = SaveConfigHandler(self)

    # when the focus is on the console entry box, the user can scroll through past commands.
    # these are stored in user_cmds with the index of the most recent command at 0
    # Every time the user enters a command, the user_cmd_index is changed to -1
    def iterate_cmds(self, keypress_event):
        if keypress_event.keycode == 111 or keypress_event.keycode == 38:  # up arrow on linux and windows, respectively

            if len(self.user_cmds) > self.user_cmd_index + 1 and len(self.user_cmds) > 0:
                self.user_cmd_index = self.user_cmd_index + 1
                last = self.user_cmds[self.user_cmd_index]
                self.console_entry.delete(0, 'end')
                self.console_entry.insert(0, last)

        elif keypress_event.keycode == 116 or keypress_event.keycode == 40:  # down arrow on linux and windows, respectively
            if self.user_cmd_index > 0:
                self.user_cmd_index = self.user_cmd_index - 1
                next = self.user_cmds[self.user_cmd_index]
                self.console_entry.delete(0, 'end')
                self.console_entry.insert(0, next)

    def reset(self):
        self.clear_queue()
        self.overwrite_all = False
        self.script_running = False
        self.script_failed = False
        self.white_referencing = False

    # execute a command either input into the console by the user or loaded from a script
    def execute_cmd(self, event):
        if self.script_running:
            self.complete_queue_item()
        # self.cmd_complete=False

        self.text_only = True
        command = self.console_entry.get()
        self.user_cmds.insert(0, command)
        self.user_cmd_index = -1
        if command != 'end file':
            self.console_log.insert(END, '>>> ' + command + '\n')
        self.console_entry.delete(0, 'end')
        thread = Thread(target=self.execute_cmd_2, kwargs={'cmd': command})
        thread.start()

    def execute_cmd_2(self,
                      cmd):  # In a separate method because that allows it to be spun off in a new thread, so tkinter mainloop continues, which means that the console log gets updated immediately e.g. if you say sleep(10) it will say sleep up in the log while it is sleeping.
        print('Command is: ' + cmd)

        def get_val(param):
            return param.split('=')[1].strip(' ').strip('"').strip("'")

        if cmd == 'wr()':
            if not self.script_running:
                self.queue = []
            self.queue.insert(0, {self.wr: [True, False]})
            self.queue.insert(1, {self.take_spectrum: [True, True, False]})
            self.wr(True, False)
        elif cmd == 'opt()':
            if not self.script_running:
                self.queue = []
            self.queue.insert(0, {self.opt: [True, False]})
            self.opt(True, False)  # override=True, setup complete=False
        elif cmd == 'goniometer.configure(MANUAL)':
            self.set_manual_automatic(force=0)

        elif 'goniometer.configure(' in cmd:
            try:
                if 'AUTOMATIC' in cmd:
                    # e.g. goniometer.configure(AUTOMATIC,-30,50,wr)
                    params = cmd[0:-1].split('goniometer.configure(AUTOMATIC')[1].split(',')[1:]
                    for i in range(len(params)):
                        params[i] = params[i].strip(' ')
                elif 'MANUAL' in cmd:
                    params = cmd[0:-1].split('goniometer.configure(MANUAL')[1].split(',')[1:]
                    params.append(1)
                else:
                    self.log('Error: invalid arguments for mode, i, e, az, sample_num: ' + str(
                        params) + '\nExample input: goniometer.configure(AUTOMATIC, 0, 20, wr)')
                    self.queue = []
                    self.script_running = False

                valid_i = validate_int_input(params[0], self.min_motor_i, self.max_motor_i)
                valid_e = validate_int_input(params[1], self.min_motor_e, self.max_motor_e)
                valid_az = valideate_int_input(params[2], self.min_motor_az, self.max_motor_az)

                valid_sample = validate_int_input(params[2], 1, int(self.num_samples))
                if params[2] == 'wr':
                    valid_sample = True
                if valid_i and valid_e and valid_az and valid_sample:
                    self.motor_i = params[0]
                    self.motor_e = params[1]
                    self.motor_az = params[2]

                    if params[3] == 'wr':
                        self.sample_tray_index = -1
                    else:
                        self.sample_tray_index = int(params[
                                                         3]) - 1  # this is used as an index where available_sample_positions[4]=='Sample 5' so it should be one less than input.

                    if 'AUTOMATIC' in cmd:
                        self.set_manual_automatic(force=1, known_goniometer_state=True)
                    else:
                        self.set_manual_automatic(force=0)
                    self.incidence_entries[0].delete(0, 'end')
                    self.incidence_entries[0].insert(0, params[0])
                    self.emission_entries[0].delete(0, 'end')
                    self.emission_entries[0].insert(0, params[1])
                    self.azimuth_entries[0].insert(0, params[2])
                    self.configure_pi(params[0], params[1], params[2], params[3], params[4])

                else:
                    self.log('Error: invalid arguments for mode, i, e, az, sample_num: ' + str(
                        params) + '\nExample input: goniometer.configure(AUTOMATIC, 0, 20, 90, wr)')
                    self.queue = []
                    self.script_running = False

            except Exception as e:
                self.fail_script_command('Error: could not parse command ' + cmd)
        elif cmd == 'collect_garbage()':
            if not self.script_running:
                self.queue = []
            self.queue.insert(0, {self.take_spectrum: [True, False, True]})
            self.take_spectrum(True, False, True)
        elif cmd == 'acquire()':
            if not self.script_running:
                self.queue = []
            self.acquire()
        elif cmd == 'take_spectrum()':
            if not self.script_running:
                self.queue = []
            self.queue.insert(0, {self.take_spectrum: [True, True, False]})
            self.take_spectrum(True, True, False)
        # e.g. set_spec_save(directory=R:\RiceData\Kathleen\test_11_15, basename=test,num=0000)
        elif 'setup_geom(' in cmd:  # params are i, e, index=0
            params = cmd[0:-1].split('setup_geom(')[1].split(',')
            if len(params) != 2 and len(params) != 3:
                self.fail_script_command('Error: could not parse command ' + cmd)
            elif self.manual_automatic.get() == 0:  # manual mode
                valid_i = validate_int_input(params[0], self.min_motor_i, self.max_motor_i)
                valid_e = validate_int_input(params[1], self.min_motor_i, self.max_motor_i)
                valid_az = validate_int_input(params[2], self.min_motor_az, self.max_motor_az)
                if not valid_i or not valid_e or not valid_az:
                    self.log('Error: i=' + params[0] + ', e=' + params[1] + ', az=' + params[
                        2] + ' is not a valid viewing geometry.')
                else:
                    self.incidence_entries[0].delete(0, 'end')
                    self.incidence_entries[0].insert(0, params[0])
                    self.emission_entries[0].delete(0, 'end')
                    self.emission_entries[0].insert(0, params[1])
                    self.azimuth_entries[0].delete(0, 'end')
                    self.azimuth_entries[0].insert(0, params[2])
            else:  # automatic mode
                valid_i = validate_int_input(params[0], self.min_motor_i, self.max_motor_i)
                valid_e = validate_int_input(params[1], self.min_motor_e, self.max_motor_e)
                valid_az = validate_int_input(params[2], self.min_motor_az, self.max_motor_az)

                if not valid_i or not valid_e or not valid_az:
                    self.log('Error: i=' + params[0] + ', e=' + params[1] + ', az=' + params[
                        1] + ' is not a valid viewing geometry.')
                else:
                    index = 0
                    if len(params) == 3:
                        index = int(get_val(params[2]))
                    valid_index = validate_int_input(index, 0, len(self.emission_entries) - 1)
                    if not valid_index:
                        self.log('Error: ' + str(index) + ' is not a valid index. Enter a value from 0-' + str(
                            len(self.emission_entries) - 1))
                    else:
                        self.incidence_entries[index].delete(0, 'end')
                        self.incidence_entries[index].insert(0, params[0])
                        self.emission_entries[index].delete(0, 'end')
                        self.emission_entries[index].insert(0, params[1])
                        self.azimuth_entires[index].delete(0, 'end')
                        self.azimuth_entries[index].insert(0, params[2])
        elif 'add_geom(' in cmd:  # params are i, e. Will not overwrite existing geom.
            params = cmd[0:-1].split('add_geom(')[1].split(',')
            if len(params) != 2:
                self.fail_script_command('Error: could not parse command ' + cmd)
            elif self.manual_automatic.get() == 0:  # manual mode
                valid_i = validate_int_input(params[0], self.min_science_i, self.max_science_i)
                valid_e = validate_int_input(params[1], self.min_science_e, self.max_science_e)
                valid_az = validate_int_input(params[2], self.min_science_az, self.max_science_az)

                if not valid_i or not valid_e or not valid_az:
                    self.log('Error: i=' + params[0] + ', e=' + params[1] + ', az=' + params[
                        2] + ' is not a valid viewing geometry.')
                elif self.emission_entries[0].get() == '' and self.incidence_entries[0].get() == '' and \
                        self.azimuth_entries[0].get() == '':
                    self.incidence_entries[0].insert(0, params[0])
                    self.emission_entries[0].insert(0, params[1])
                    self.azimuth_entries[0].insert(0, params[2])
                else:
                    self.log('Error: Cannot add second geometry in manual mode.')
            else:  # automatic mode
                if self.individual_range.get() == 1:
                    self.log('Error: Cannot add geometry in range mode. Use setup_geom_range() instead')
                else:
                    valid_i = validate_int_input(params[0], self.min_science_i, self.max_science_i)
                    valid_e = validate_int_input(params[1], self.min_science_e, self.max_science_e)
                    valid_az = validate_int_input(params[2], self.min_science_az, self.max_science_az)

                    if not valid_i or not valid_e or not valid_az:
                        self.log('Error: i=' + params[0] + ', e=' + params[1] + ', az=' + params[
                            2] + ' is not a valid viewing geometry.')
                    elif self.emission_entries[0].get() == '' and self.incidence_entries[0].get() == '':
                        self.incidence_entries[0].insert(0, params[0])
                        self.emission_entries[0].insert(0, params[1])
                        self.azimuth_entries[0].insert(0, params[2])
                    else:
                        self.add_geometry()
                        self.incidence_entries[-1].insert(0, params[0])
                        self.emission_entries[-1].insert(0, params[1])
                        self.azimuth_entries[-1].insert(0, params[2])




        elif 'setup_geom_range(' in cmd:
            if self.manual_automatic.get() == 0:
                self.log('Error: Not in automatic mode')
                self.queue = []
                self.script_running = False
                return False
            self.set_individual_range(force=1)
            params = cmd[0:-1].split('setup_geom_range(')[1].split(',')
            for param in params:
                if 'i_start' in param:
                    try:
                        self.light_start_entry.delete(0, 'end')
                        self.light_start_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse initial incidence angle')
                        self.queue = []
                        self.script_running = False
                elif 'i_end' in param:
                    try:
                        self.light_end_entry.delete(0, 'end')
                        self.light_end_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse final incidence angle')
                        self.queue = []
                        self.script_running = False
                elif 'e_start' in param:
                    try:
                        self.detector_start_entry.delete(0, 'end')
                        self.detector_start_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse initial emission angle')
                        self.queue = []
                        self.script_running = False
                elif 'e_end' in param:
                    try:
                        self.detector_end_entry.delete(0, 'end')
                        self.detector_end_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse final emission angle')
                        self.queue = []
                        self.script_running = False
                elif 'az_start' in param:
                    try:
                        self.azimuth_start_entry.delete(0, 'end')
                        self.azimuth_start_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse initial azimuth angle')
                        self.queue = []
                        self.script_running = False
                elif 'az_end' in param:
                    try:
                        self.azimuth_end_entry.delete(0, 'end')
                        self.azimuth_end_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse final azimuth angle')
                        self.queue = []
                        self.script_running = False
                elif 'i_increment' in param:
                    try:
                        self.light_increment_entry.delete(0, 'end')
                        self.light_increment_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse incidence angle increment.')
                        self.queue = []
                        self.script_running = False
                elif 'e_increment' in param:
                    try:
                        self.detector_increment_entry.delete(0, 'end')
                        self.detector_increment_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse emission angle increment.')
                        self.queue = []
                        self.script_running = False
                elif 'az_increment' in param:
                    try:
                        self.azimuth_increment_entry.delete(0, 'end')
                        self.azimuth_increment_entry.insert(0, get_val(param))
                    except:
                        self.log('Error: Unable to parse azimuth angle increment.')
                        self.queue = []
                        self.script_running = False
            if len(self.queue) > 0:
                self.next_in_queue()
        elif 'set_samples(' in cmd:
            params = cmd[0:-1].split('set_samples(')[1].split(',')
            if params == ['']: params = []

            # First clear all existing sample names
            while len(self.sample_frames) > 1:
                self.remove_sample(-1)
            self.set_text(self.sample_label_entries[0], '')

            # Then add in samples in order specified in params. Each param should be a sample name and pos.
            skip_count = 0  # If a param is badly formatted, we'll skip it. Keep track of how many are skipped in order to index labels, etc right.
            for i, param in enumerate(params):

                try:
                    pos = param.split('=')[0].strip(' ')
                    name = get_val(param)
                    valid_pos = validate_int_input(pos, 1, 5)
                    if self.available_sample_positions[int(
                            pos) - 1] in self.taken_sample_positions:  # If the requested position is already taken, we're not going to allow it.
                        if len(
                                self.sample_label_entries) > 1:  # If only one label is out there, it will be listed as taken even though the entry is empty, so we can ignore it. But if there is more than one label, we know the position is a repeat and not valid.
                            valid_pos = False
                        elif self.sample_label_entries[
                            0].get() != '':  # Even if there is only one label, if the entry has already been filled in then the position is a repeat and not valid.
                            valid_pos = False
                    if i - skip_count != 0 and valid_pos:
                        self.add_sample()
                except:  # If the position isn't specified, fail.
                    self.log(
                        'Error: could not parse command ' + cmd + '. Use the format set_samples({position}={name}) e.g. set_samples(1=Basalt)')
                    skip_count += 1

                if valid_pos:
                    self.set_text(self.sample_label_entries[i - skip_count], name)
                    self.sample_pos_vars[i - skip_count].set(self.available_sample_positions[int(pos) - 1])
                    self.set_taken_sample_positions()
                else:
                    self.log(
                        'Error: ' + pos + ' is an invalid sample position. Use the format set_samples({position}={1}) e.g. set_samples(1=Basalt). Do not repeat sample positions.')
                    skip_count += 1

            if len(self.queue) > 0:
                self.next_in_queue()

        elif 'set_spec_save(' in cmd:
            self.unfreeze()
            params = cmd[0:-1].split('set_spec_save(')[1].split(',')

            for i, param in enumerate(params):
                params[i] = param.strip(' ')  # Need to do this before looking for setup only
                if 'directory' in param:
                    dir = get_val(param)
                    self.spec_save_dir_entry.delete(0, 'end')
                    self.spec_save_dir_entry.insert(0, dir)
                elif 'basename' in param:
                    basename = get_val(param)
                    self.spec_basename_entry.delete(0, 'end')
                    self.spec_basename_entry.insert(0, basename)
                elif 'num' in param:
                    num = get_val(param)
                    self.spec_startnum_entry.delete(0, 'end')
                    self.spec_startnum_entry.insert(0, num)

            if not self.script_running:
                self.queue = []

            # If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI is just filled in for them how they want.
            setup_only = False

            if 'setup_only=True' in params:
                setup_only = True
            elif 'setup_only =True' in params:
                setup_only = True
            elif 'setup_only = True' in params:
                setup_only = True

            if not setup_only:
                self.queue.insert(0, {self.set_save_config: []})
                self.set_save_config()
            elif len(self.queue) > 0:
                self.next_in_queue()
        elif 'instrument.configure(' in cmd:
            params = cmd[0:-1].split('instrument.configure(')[1].split(',')
            for i, param in enumerate(params):
                params[i] = param.strip(' ')  # needed when we check for setup_only
            try:
                num = int(params[0])
                self.instrument_config_entry.delete(0, 'end')
                self.instrument_config_entry.insert(0, str(num))
                if not self.script_running:
                    self.queue = []

                # If the user uses the setup_only option, no commands are sent to the spec computer, but instead the GUI is just filled in for them how they want.
                setup_only = False
                if 'setup_only=True' in params:
                    setup_only = True
                elif 'setup_only =True' in params:
                    setup_only = True
                elif 'setup_only = True' in params:
                    setup_only = True

                if not setup_only:
                    self.queue.insert(0, {self.configure_instrument: []})
                    self.configure_instrument()
                elif len(self.queue) > 0:
                    self.next_in_queue()
            except:
                self.fail_script_command('Error: could not parse command ' + cmd)


        elif 'sleep' in cmd:
            param = cmd[0:-1].split('sleep(')[1]
            try:
                num = float(param)
                try:
                    title = 'Sleeping...'
                    label = 'Sleeping...'
                    self.wait_dialog.reset(title=title, label=label)
                except:
                    pass  # If there isn't already a wait dialog up, don't create one.
                elapsed = 0
                while elapsed < num - 10:
                    time.sleep(10)
                    elapsed += 10
                    self.console_log.insert(END, '\t' + str(elapsed))
                remaining = num - elapsed
                time.sleep(remaining)
                # self.cmd_complete==True
                self.console_log.insert(END, '\tDone sleeping.\n')
                if len(self.queue) > 0:
                    self.next_in_queue()
            except:
                self.fail_script_command('Error: could not parse command ' + cmd)


        elif 'move_tray(' in cmd:
            if self.manual_automatic.get() == 0:
                self.log('Error: Not in automatic mode')
                return False
            try:
                param = cmd.split('move_tray(')[1].strip(')')
            except:
                self.fail_script_command('Error: could not parse command ' + cmd)
                return False
            if 'steps' in param:
                try:
                    steps = int(param.split('=')[-1])
                    valid_steps = validate_int_input(steps, -800, 800)

                except:
                    self.fail_script_command('Error: could not parse command ' + cmd)
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.move_tray: [steps, 'steps']})
                    self.move_tray(steps, type='steps')
                else:
                    self.log(
                        'Error: ' + str(steps) + ' is not a valid number of steps. Enter an integer from -800 to 800.')
                    self.queue = []
                    self.script_running = False
                    return False
            else:
                pos = param
                alternatives = ['1', '2', '3', '4',
                                '5']  # These aren't how sample positions are specified in available_sample_positions (which has Sample 1, etc) but we'll accept them.
                if pos in alternatives:
                    pos = self.available_sample_positions[alternatives.index(pos)]
                elif pos.lower() == 'wr':
                    pos = pos.lower()
                if pos in self.available_sample_positions or pos == 'wr':

                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.move_tray: [pos]})
                    self.move_tray(pos)
                else:
                    self.log('Error: ' + pos + ' is an invalid tray position')
                    self.queue = []
                    self.script_running = False
                    return False

        elif 'set_emission(' in cmd:
            if self.manual_automatic.get() == 0 or PI_OFFLINE:
                print(self.manual_automatic.get())
                self.log('Error: Not in automatic mode')
                self.queue = []
                self.script_running = False
                return False
            try:
                param = cmd.split('set_emission(')[1][:-1]

            except:
                self.fail_script_command('Error: could not parse command ' + cmd)
                return False

            if 'steps' in param:
                try:
                    steps = int(param.split('=')[-1])
                    valid_steps = validate_int_input(steps, -1000, 1000)

                except:
                    self.fail_script_command('Error: could not parse command ' + cmd)
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.set_emission: [steps, 'steps']})
                    self.set_emission(steps, 'steps')
                else:
                    self.log('Error: ' + str(
                        steps) + ' is not a valid number of steps. Enter an integer from -1000 to 1000.')
                    self.queue = []
                    self.script_running = False
                    return False
            else:
                e = param
                valid_e = validate_int_input(e, self.min_science_e, self.max_science_e)
                if valid_e:
                    e = int(param)
                    valid_geom = self.validate_distance(self.science_i, e, self.science_az)
                    #                     if not valid_geom:
                    #                         self.log('Error: Because of geometric constraints on the instrument, angular separation must be at least '+str(self.required_angular_separation)+' degrees')
                    #                         self.queue=[]
                    #                         self.script_running=False
                    #                         return False

                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.set_emission: [e]})
                    self.set_emission(e)
                else:
                    self.log('Error: ' + str(e) + ' is an invalid emission angle.')
                    self.queue = []
                    self.script_running = False
                    return False

        elif 'set_azimuth(' in cmd:
            if self.manual_automatic.get() == 0 or PI_OFFLINE:
                self.log('Error: Not in automatic mode')
                self.queue = []
                self.script_running = False
                return False
            try:
                param = cmd.split('set_azimuth(')[1][:-1]

            except:
                self.fail_script_command('Error: could not parse command ' + cmd)
                return False

            if 'steps' in param:
                try:
                    steps = int(param.split('=')[-1])
                    valid_steps = validate_int_input(steps, -1000, 1000)

                except:
                    self.fail_script_command('Error: could not parse command ' + cmd)
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.set_emission: [steps, 'steps']})
                    self.set_emission(steps, 'steps')
                else:
                    self.log('Error: ' + str(
                        steps) + ' is not a valid number of steps. Enter an integer from -1000 to 1000.')
                    self.queue = []
                    self.script_running = False
                    return False
            else:
                az = param
                valid_az = validate_int_input(az, self.min_science_az, self.max_science_az)
                if valid_az:
                    valid_geom = self.validate_distance(self.science_i, self.science_e, int(az))
                    #                     if not valid_geom:
                    #                         self.log('Error: Because of geometric constraints on the instrument, angular separation must be at least '+str(self.required_angular_separation)+' degrees')
                    #                         self.queue=[]
                    #                         self.script_running=False
                    #                         return False

                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.set_azimuth: [az]})
                    self.set_azimuth(az)
                else:
                    self.log('Error: ' + str(az) + ' is an invalid azimuth angle.')
                    self.queue = []
                    self.script_running = False
                    return False


        # Accepts incidence angle in degrees, converts to motor position. OR accepts motor steps to move.
        elif 'set_incidence(' in cmd:
            if self.manual_automatic.get() == 0 or PI_OFFLINE:
                self.log('Error: Not in automatic mode')
                self.queue = []
                self.script_running = False
                return False
            try:
                param = cmd.split('set_incidence(')[1][:-1]

            except:
                self.fail_script_command('Error: could not parse command ' + cmd)
                return False

            if 'steps' in param:
                try:
                    steps = int(param.split('=')[-1])
                    valid_steps = validate_int_input(steps, -1000, 1000)

                except:
                    self.fail_script_command('Error: could not parse command ' + cmd)
                    return False
                if valid_steps:
                    if not self.script_running:
                        self.queue = []
                    self.queue.insert(0, {self.set_incidence: [steps, 'steps']})
                    self.set_incidence(steps, 'steps')
                else:
                    self.log('Error: ' + str(
                        steps) + ' is not a valid number of steps. Enter an integer from -1000 to 1000.')
                    self.queue = []
                    self.script_running = False
                    return False
            else:
                next_science_i = param
                valid_i = validate_int_input(next_science_i, self.min_science_i, self.max_science_i)
                if valid_i:
                    next_science_i = int(next_science_i)
                    valid_geom = self.validate_distance(next_science_i, self.science_e, self.science_az)

                    if not self.script_running:
                        self.queue = []

                    if self.motor_az >= 180 or self.motor_az < 0:
                        next_motor_i = -1 * next_science_i
                    else:
                        next_motor_i = next_science_i

                    self.queue.insert(0, {self.set_incidence: [next_motor_i]})
                    self.set_incidence(next_motor_i)
                else:
                    self.log('Error: ' + next_science_i + ' is an invalid incidence angle.')
                    self.queue = []
                    self.script_running = False
                    return False

        elif 'set_motor_azimuth' in cmd:
            if self.manual_automatic.get() == 0 or PI_OFFLINE:
                self.log('Error: Not in automatic mode')
                self.queue = []
                self.script_running = False
                return False
            az = int(cmd.split('set_motor_azimuth(')[1].strip(')'))
            valid_az = validate_int_input(az, self.min_motor_az, self.max_motor_az)

            if valid_az:
                next_science_i, next_science_e, next_science_az = self.motor_pos_to_science_pos(self.motor_i,
                                                                                                self.motor_e, int(az))
                valid_geom = self.validate_distance(next_science_i, next_science_e, next_science_az)

                if not self.script_running:
                    self.queue = []
                self.queue.insert(0, {self.set_azimuth: [az]})
                self.set_azimuth(az)
            else:
                self.log('Error: ' + str(az) + ' is an invalid azimuth angle.')
                self.queue = []
                self.script_running = False
                return False

        elif 'set_goniometer' in cmd:
            params = cmd.split('set_goniometer(')[1].strip(')').split(',')
            if len(params) != 3:
                self.log(str(len(params)))
                self.log('Error: invalid display setting. Enter set_display(i, e, az')
                return

            valid_i = validate_int_input(params[0], self.min_science_i, self.max_science_i)
            valid_e = validate_int_input(params[1], self.min_science_e, self.max_science_e)
            valid_az = validate_int_input(params[2], self.min_science_az, self.max_science_az)

            if not valid_i or not valid_e or not valid_az:
                self.log('Error: invalid geometry')
                return

            i = int(params[0])
            e = int(params[1])
            az = int(params[2])

            current_motor = (self.motor_i, self.motor_e, self.motor_az)
            movements = self.get_movements(i, e, az, current_motor=current_motor)

            if movements == None:
                print('NO PATH FOUND')
                self.log(
                    'Error: Cannot find a path from current geometry to i= ' + str(i) + ', e=' + str(e) + ', az=' + str(
                        az))

            else:
                temp_queue = []

                for movement in movements:
                    if 'az' in movement:
                        next_motor_az = movement['az']
                        temp_queue.append({self.set_azimuth: [next_motor_az]})
                    elif 'e' in movement:
                        next_motor_e = movement['e']
                        temp_queue.append({self.set_emission: [next_motor_e]})
                    elif 'i' in movement:
                        next_motor_i = movement['i']
                        temp_queue.append({self.set_incidence: [next_motor_i]})
                    else:
                        print('UNEXPECTED: ' + str(movement))

                self.queue = temp_queue + self.queue

            if len(self.queue) > 0:
                self.next_in_queue()
            else:
                self.script_running = False
                self.queue = []
        elif cmd == 'print_movements()':
            print(len(self.goniometer_view.movements['i']))
            print(len(self.goniometer_view.movements['e']))
            print(len(self.goniometer_view.movements['az']))
            print()
            print(self.goniometer_view.movements)
            print()

            if len(self.queue) > 0:
                self.next_in_queue()
            else:
                self.script_running = False
                self.queue = []



        elif 'set_display' in cmd:
            params = cmd.split('set_display(')[1].strip(')').split(',')
            if len(params) != 3:
                self.log(str(len(params)))
                self.log('Error: invalid display setting. Enter set_display(i, e, az')
                return

            valid_i = validate_int_input(params[0], self.min_science_i, self.max_science_i)
            valid_e = validate_int_input(params[1], self.min_science_e, self.max_science_e)
            valid_az = validate_int_input(params[2], self.min_science_az, self.max_science_az)

            if not valid_i or not valid_e or not valid_az:
                self.log('Error: invalid geometry')
                if len(self.queue) > 0:
                    self.next_in_queue()
                    return
                else:
                    self.script_running = False
                    self.queue = []
                    return

            i = int(params[0])
            e = int(params[1])
            az = int(params[2])

            current_motor = (self.goniometer_view.motor_i, self.goniometer_view.motor_e, self.goniometer_view.motor_az)
            movements = self.get_movements(i, e, az, current_motor=current_motor)

            current_science_i = self.goniometer_view.science_i
            current_science_e = self.goniometer_view.science_e
            current_science_az = self.goniometer_view.science_az

            if movements == None:
                print('NO PATH FOUND')
                self.log(
                    'Error: Cannot find a path from current geometry to i= ' + str(i) + ', e=' + str(e) + ', az=' + str(
                        az))

            #                 movements=self.get_movements(e, i, az, current_motor=current_motor)
            #                 if movements==None:
            #                     movements=self.get_movements(-1*i, -1*e, az, current_motor=current_motor)
            #                     if movements==None:
            #                         movements=self.get_movements(-1*e, -1*i, az, current_motor=current_motor)
            #
            #                 if movements==None:
            #                     print('NO PATH FOUND')
            #                     self.log('Error: Cannot find a path from current geometry to i= '+str(i)+', e='+str(e)+', az='+str(az))
            #                 else:
            #                     print('RECIPROCAL')
            #                     self.log('Warning! Using reciprocal geometry instead for '+str(e)+' '+str(i)+' '+str(az))

            if movements != None:
                temp_queue = []

                for movement in movements:
                    if 'az' in movement:
                        next_motor_az = movement['az']
                        temp_queue.append({self.goniometer_view.set_azimuth: [next_motor_az]})
                    elif 'e' in movement:
                        next_motor_e = movement['e']
                        temp_queue.append({self.goniometer_view.set_emission: [next_motor_e]})
                    elif 'i' in movement:
                        next_motor_i = movement['i']
                        temp_queue.append({self.goniometer_view.set_incidence: [next_motor_i]})
                    else:
                        print('UNEXPECTED: ' + str(movement))

                for item in temp_queue:
                    for func in item:
                        args = item[func]
                        func(*args)

            if len(self.queue) > 0:
                self.next_in_queue()
            else:
                self.script_running = False
                self.queue = []

        #             valid_geom=self.validate_distance(i,e, az)
        #             if not valid_geom:
        #                 self.log('Error: Geometric constraints on the instrument make this position impossible to reach.')
        #                 if len(self.queue)>0:
        #                     self.next_in_queue()
        #                 else:
        #                     self.script_running=False
        #                     self.queue=[]
        #                 return
        #
        #
        #             current_motor=(self.goniometer_view.motor_i,self.goniometer_view.motor_e, self.goniometer_view.motor_az)
        #             movements=self.get_movements(i,e,az, current_motor=current_motor)
        #
        #             current_science_i=self.goniometer_view.science_i
        #             current_science_e=self.goniometer_view.science_e
        #             current_science_az=self.goniometer_view.science_az
        #
        #             if movements==None:
        #                 print('NO PATH FOUND')
        #                 self.log('Error: Cannot find a path from current geometry to i= '+str(i)+', e='+str(e)+', az='+str(az))
        #
        #             else:
        #                 temp_queue=[]
        #
        #                 for movement in movements:
        #                     if 'az' in movement:
        #                         next_motor_az=movement['az']
        #                         temp_queue.append({self.goniometer_view.set_azimuth:[next_motor_az]})
        #                     elif 'e' in movement:
        #                         next_motor_e=movement['e']
        #                         temp_queue.append({self.goniometer_view.set_emission:[next_motor_e]})
        #                     elif 'i' in movement:
        #                         next_motor_i=movement['i']
        #                         temp_queue.append({self.goniometer_view.set_incidence:[next_motor_i]})
        #                     else:
        #                         print('UNEXPECTED: '+str(movement))
        #
        #                 for item in temp_queue:
        #                     for func in item:
        #                         args=item[func]
        #                         func(*args)
        #
        #
        #             if len(self.queue)>0:
        #                 self.next_in_queue()
        #             else:
        #                 self.script_running=False
        #                 self.queue=[]
        #
        elif 'rotate_display' in cmd:
            angle = cmd.split('rotate_display(')[1].strip(')')
            valid = validate_int_input(angle, -360, 360)
            if not valid:
                self.log('Error: invalid geometry')
                return
            else:
                angle = int(angle)

            self.goniometer_view.set_goniometer_tilt(0)

            self.goniometer_view.wireframes['i'].rotate_az(angle)
            self.goniometer_view.wireframes['light'].rotate_az(angle)
            self.goniometer_view.wireframes['light guide'].rotate_az(angle)
            self.goniometer_view.wireframes['motor az guide'].rotate_az(angle)
            self.goniometer_view.wireframes['science az guide'].rotate_az(angle)

            self.goniometer_view.wireframes['e'].rotate_az(angle)
            self.goniometer_view.wireframes['detector'].rotate_az(angle)
            self.goniometer_view.wireframes['detector guide'].rotate_az(angle)

            self.goniometer_view.set_goniometer_tilt(20)

            self.goniometer_view.draw_3D_goniometer(self.goniometer_view.width, self.goniometer_view.height)
            self.goniometer_view.flip()

        elif 'rotate_tray_display' in cmd:
            angle = cmd.split('rotate_tray_display(')[1].strip(')')
            valid = validate_int_input(angle, -360, 360)
            if not valid:
                self.log('Error: invalid geometry')
                return
            else:
                angle = int(angle)
            self.goniometer_view.rotate_tray(angle)
            self.goniometer_view.draw_3D_goniometer(self.goniometer_view.width, self.goniometer_view.height)
            self.goniometer_view.flip()

        elif cmd == 'end file':
            self.script_running = False
            self.queue = []
            if self.wait_dialog != None:
                self.wait_dialog.interrupt(
                    'Success!')  # If there is a wait dialog up, make it say success. There may never have been one that was made though.
                self.wait_dialog.top.wm_geometry('376x140')
            return True

        else:
            self.fail_script_command('Error: could not parse command ' + cmd)
            return False

        self.text_only = False
        return True

    def fail_script_command(self, message):
        self.log(message)
        self.queue = []
        self.script_running = False
        if self.wait_dialog != None:
            self.wait_dialog.interrupt(message)
            self.wait_dialog.top.wm_geometry('376x140')

    def increment_num(self):
        try:
            num = int(self.spec_startnum_entry.get()) + 1
            self.spec_startnum_entry.delete(0, 'end')
            self.spec_startnum_entry.insert(0, str(num))
        except:
            return

    def move(self):
        try:
            incidence = int(man_light_entry.get())
            emission = int(man_detector_entry.get())
        except:
            return
        if incidence < 0 or incidence > 90 or emission < 0 or emission > 90:
            return
        # self.model.move_light(i)
        # self.model.move_detector(e)

    def check_local_folder(self, dir, next_action):
        def try_mk_dir(dir, next_action):
            try:
                os.makedirs(dir)
                next_action()
            except Exception as e:
                dialog = ErrorDialog(self, title='Cannot create directory', label='Cannot create directory:\n\n' + dir)
            return False

        exists = os.path.exists(dir)
        if exists:
            # If the file exists, try creating and deleting a new file there to make sure we have permission.
            try:
                if self.opsys == 'Linux' or self.opsys == 'Mac':
                    if dir[-1] != '/':
                        dir += '/'
                else:
                    if dir[-1] != '\\':
                        dir += '\\'

                existing = os.listdir(dir)
                i = 0
                delme = 'delme' + str(i)
                while delme in existing:
                    i += 1
                    delme = 'delme' + str(i)

                os.mkdir(dir + delme)
                os.rmdir(dir + delme)
                return True

            except:
                dialog = ErrorDialog(self, title='Error: Cannot write',
                                     label='Error: Cannot write to specified directory.\n\n' + dir)
                return False
        else:
            if self.script_running:  # If we're running a script, just try making the directory automatically.
                try_mk_dir(dir, next_action)
            else:  # Otherwise, ask the user.
                buttons = {
                    'yes': {
                        try_mk_dir: [dir, next_action]
                    },
                    'no': {
                    }
                }
                dialog = ErrorDialog(self, title='Directory does not exist',
                                     label=dir + '\n\ndoes not exist. Do you want to create this directory?',
                                     buttons=buttons)
        return exists

    # Checks if the given directory exists and is writeable. If not writeable, gives user option to create.
    def check_remote_folder(self, dir, next_action):

        def inner_mkdir(dir, next_action):
            status = self.remote_directory_worker.mkdir(dir)
            if status == 'mkdirsuccess':
                next_action()
            elif status == 'mkdirfailedfileexists':
                dialog = ErrorDialog(self, title='Error',
                                     label='Could not create directory:\n\n' + dir + '\n\nFile exists.')
            elif status == 'mkdirfailed':
                dialog = ErrorDialog(self, title='Error', label='Could not create directory:\n\n' + dir)

        status = self.remote_directory_worker.get_dirs(self.spec_save_dir_entry.get())

        if status == 'listdirfailed':
            buttons = {
                'yes': {
                    inner_mkdir: [dir, next_action]
                },
                'no': {
                }
            }
            dialog = ErrorDialog(self, title='Directory does not exist',
                                 label=dir + '\ndoes not exist. Do you want to create this directory?', buttons=buttons)
            return False
        elif status == 'listdirfailedpermission':
            dialog = ErrorDialog(self, label='Error: Permission denied for\n' + dir)
            return False

        elif status == 'timeout':
            if not self.text_only:
                buttons = {
                    'cancel': {},
                    'retry': {self.spec_commander.remove_from_listener_queue: [['timeout']], self.next_in_queue: []}
                }
                dialog = ErrorDialog(self,
                                     label='Error: Operation timed out.\n\nCheck that the automation script is running on the spectrometer\n computer and the spectrometer is connected.',
                                     buttons=buttons)
                for button in dialog.tk_buttons:
                    button.config(width=15)
            else:
                self.log('Error: Operation timed out.')
            return False

        self.spec_commander.check_writeable(dir)
        t = 3 * BUFFER
        while t > 0:
            if 'yeswriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('yeswriteable')
                return True
            elif 'notwriteable' in self.spec_listener.queue:
                self.spec_listener.queue.remove('notwriteable')
                dialog = ErrorDialog(self, label='Error: Permission denied.\nCannot write to specified directory.')
                return False
            time.sleep(INTERVAL)
            t = t - INTERVAL
        if t <= 0:
            dialog = ErrorDialog(self, label='Error: Operation timed out.')
            return False

    def check_local_file(self, directory, file, next_action):
        def remove_retry(file, next_action):
            try:
                os.remove(file)
                next_action()
            except:
                dialog = ErrorDialog(self, title='Error overwriting file',
                                     label='Error: Could not delete file.\n\n' + file)

        if self.opsys == 'Linux' or self.opsys == 'Mac':
            if directory[-1] != '/':
                directory += '/'
        else:
            if directory[-1] != '\\':
                directory += '\\'

        self.full_process_output_path = directory + file
        if os.path.exists(self.full_process_output_path):
            buttons = {
                'yes': {
                    remove_retry: [self.full_process_output_path, next_action]
                },
                'no': {
                }
            }
            dialog = Dialog(self, title='Error: File Exists',
                            label='Error: Specified output file already exists.\n\n' + self.full_process_output_path + '\n\nDo you want to overwrite this data?',
                            buttons=buttons)
            dialog.top.wm_geometry('376x175')
            return False
        else:
            return True

    def process_cmd(self):

        output_file = self.output_file_entry.get()

        if output_file == '':
            dialog = ErrorDialog(self, label='Error: Enter an output file name')
            return

        if output_file[-4:] != '.csv':
            output_file = output_file + '.csv'
            self.output_file_entry.insert('end', '.csv')

        self.full_process_output_path = output_file

        input_directory = self.input_dir_entry.get()
        if input_directory[-1] == '\\':
            input_directory = input_directory[:-1]

        if self.proc_local.get() == 1:
            self.plot_local_remote = 'local'

            check = self.check_local_file(self.output_dir_entry.get(), output_file, self.process_cmd)
            if not check: return  # If the file exists, controller.check_local_file_exists gives the user the option to overwrite, in which case process_cmd gets called again.
            check = self.check_local_folder(self.output_dir_entry.get(), self.process_cmd)
            if not check: return  # Same deal for the folder (except existing is good).

            self.spec_commander.process(input_directory, 'spec_share_loc', 'proc_temp.csv')

        else:
            self.plot_local_remote = 'remote'
            output_directory = self.output_dir_entry.get()
            check = self.check_remote_folder(output_directory, self.process_cmd)
            if not check:
                return

            self.spec_commander.process(input_directory, output_directory, output_file)

        if self.process_save_dir.get():
            file = open(self.local_config_loc + 'process_directories.txt', 'w')
            file.write(self.plot_local_remote + '\n')
            file.write(self.input_dir_entry.get() + '\n')
            file.write(self.output_dir_entry.get() + '\n')
            file.write(output_file + '\n')
            file.close()

        self.queue.insert(0, {self.process_cmd: []})
        self.queue.insert(1, {self.finish_process: [output_file]})
        process_handler = ProcessHandler(self)

    def finish_process(self, output_file):
        self.complete_queue_item()
        # We're going to transfer the data file and log file to the final destination. To transfer the log file, first decide on a name to call it. This will be based on the dat file name. E.g. foo.csv would have foo_log.txt associated with it.
        final_data_destination = self.output_file_entry.get()
        if '.' not in final_data_destination:
            final_data_destination = final_data_destination + '.csv'
        data_base = '.'.join(final_data_destination.split('.')[0:-1])
        log_base = ''

        if self.opsys == 'Linux' or self.opsys == 'Mac':
            final_data_destination = self.output_dir_entry.get() + '/' + final_data_destination
            log_base = self.output_dir_entry.get() + '/' + data_base + '_log'
        else:
            final_data_destination = self.output_dir_entry.get() + '\\' + final_data_destination
            log_base = self.output_dir_entry.get() + '\\' + data_base + '_log'

        final_log_destination = log_base
        i = 1
        while os.path.isfile(final_log_destination + '.txt'):
            final_log_destination = log_base + '_' + str(i)
            i += 1
        final_log_destination += '.txt'

        for item in self.spec_listener.queue:
            if 'spec_data' in item:
                spec_data = item['spec_data']
                print('Writing data to ' + final_data_destination)
                with open(final_data_destination, 'w+') as f:
                    f.write(spec_data)

        for item in self.spec_listener.queue:
            if 'log_data' in item:
                log_data = item['log_data']
                print('Writing log file to ' + final_log_destination)
                with open(final_log_destination, 'w+') as f:
                    f.write(log_data)

    #     #Not used, replaced by open_plot_settings.
    #     def open_options(self, tab,current_title):
    #         #If the user already has dialogs open for editing the plot, close the extras to avoid confusion.
    #         self.close_plot_option_windows()
    #         def select_tab():
    #             self.view_notebook.select(tab.top)
    #         buttons={
    #             'ok':{
    #                 select_tab:[],
    #                 lambda: tab.set_title(self.new_plot_title_entry.get()):[]
    #             }
    #         }
    #         def set_markerstyle():
    #             tab.set_markerstyle(self.markerstyle_sample_var.get(), self.markerstyle_markerstyle_var.get())
    #
    #         def apply_x():
    #             self.view_notebook.select(tab.top)
    #
    #             try:
    #                 x1=float(self.left_zoom_entry.get())
    #                 x2=float(self.right_zoom_entry.get())
    #                 tab.adjust_x(x1,x2)
    #             except:
    #                 ErrorDialog(self, title='Invalid Zoom Range',label='Error: Invalid x limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
    #
    #         def apply_y():
    #             self.view_notebook.select(tab.top)
    #             try:
    #                 y1=float(self.left_zoom_entry2.get())
    #                 y2=float(self.right_zoom_entry2.get())
    #                 tab.adjust_y(y1,y2)
    #             except Exception as e:
    #                 print(e)
    #                 ErrorDialog(self, title='Invalid Zoom Range',label='Error! Invalid y limits: '+self.left_zoom_entry2.get()+', '+self.right_zoom_entry2.get())
    #
    #         def apply_z():
    #             self.view_notebook.select(tab.top)
    #
    #             try:
    #                 z1=float(self.left_zoom_entry_z.get())
    #                 z2=float(self.right_zoom_entry_z.get())
    #                 tab.adjust_z(z1,z2)
    #             except Exception as e:
    #                 print(e)
    #                 ErrorDialog(self, title='Invalid Zoom Range',label='Error: Invalid z limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
    #
    #         self.plot_options_dialog=Dialog(self,'Plot Options','\nPlot title:',buttons=buttons)
    #         self.new_plot_title_entry=Entry(self.plot_options_dialog.top, width=20, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.new_plot_title_entry.insert(0,current_title)
    #         self.new_plot_title_entry.pack()
    #
    #         self.outer_outer_zoom_frame=Frame(self.plot_options_dialog.top,bg=self.bg,padx=self.padx,pady=15)
    #         self.outer_outer_zoom_frame.pack(expand=True,fill=BOTH)
    #
    #         self.zoom_title_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg)
    #         self.zoom_title_frame.pack(pady=(5,10))
    #         self.zoom_title_label=Label(self.zoom_title_frame,text='Adjust plot x and y limits:',bg=self.bg,fg=self.textcolor)
    #         self.zoom_title_label.pack(side=LEFT,pady=(0,4))
    #
    #         self.outer_zoom_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
    #         self.outer_zoom_frame.pack(expand=True,fill=BOTH,pady=(0,10))
    #         self.zoom_frame=Frame(self.outer_zoom_frame,bg=self.bg,padx=self.padx)
    #         self.zoom_frame.pack()
    #
    #         self.zoom_label=Label(self.zoom_frame,text='x1:',bg=self.bg,fg=self.textcolor)
    #         self.left_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_label2=Label(self.zoom_frame,text='x2:',bg=self.bg,fg=self.textcolor)
    #         self.right_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_button=Button(self.zoom_frame,text='Apply',  command=apply_x,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.zoom_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #         self.zoom_button.pack(side=RIGHT,padx=(10,10))
    #         self.right_zoom_entry.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label2.pack(side=RIGHT,padx=self.padx)
    #         self.left_zoom_entry.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label.pack(side=RIGHT,padx=self.padx)
    #
    #
    #         self.outer_zoom_frame2=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
    #         self.outer_zoom_frame2.pack(expand=True,fill=BOTH,pady=(0,10))
    #         self.zoom_frame2=Frame(self.outer_zoom_frame2,bg=self.bg,padx=self.padx)
    #         self.zoom_frame2.pack()
    #         self.zoom_label3=Label(self.zoom_frame2,text='y1:',bg=self.bg,fg=self.textcolor)
    #         self.left_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_label4=Label(self.zoom_frame2,text='y2:',bg=self.bg,fg=self.textcolor)
    #         self.right_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_button2=Button(self.zoom_frame2,text='Apply',  command=apply_y,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.zoom_button2.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #
    #         self.zoom_button2.pack(side=RIGHT,padx=(10,10))
    #         self.right_zoom_entry2.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label4.pack(side=RIGHT,padx=self.padx)
    #         self.left_zoom_entry2.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label3.pack(side=RIGHT,padx=self.padx)
    #
    #         if tab.plot.x_axis=='contour':
    #             self.outer_zoom_frame_z=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
    #             self.outer_zoom_frame_z.pack(expand=True,fill=BOTH,pady=(0,10))
    #             self.zoom_frame_z=Frame(self.outer_zoom_frame_z,bg=self.bg,padx=self.padx)
    #             self.zoom_frame_z.pack()
    #             self.zoom_label_z1=Label(self.zoom_frame_z,text='z1:',bg=self.bg,fg=self.textcolor)
    #             self.left_zoom_entry_z=Entry(self.zoom_frame_z, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #             self.zoom_label_z2=Label(self.zoom_frame_z,text='z2:',bg=self.bg,fg=self.textcolor)
    #             self.right_zoom_entry_z=Entry(self.zoom_frame_z, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #             self.zoom_button_z=Button(self.zoom_frame_z,text='Apply',  command=apply_z,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #             self.zoom_button_z.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #
    #
    #
    #             self.zoom_button_z.pack(side=RIGHT,padx=(10,10))
    #             self.right_zoom_entry_z.pack(side=RIGHT,padx=self.padx)
    #             self.zoom_label_z2.pack(side=RIGHT,padx=self.padx)
    #             self.left_zoom_entry_z.pack(side=RIGHT,padx=self.padx)
    #             self.zoom_label_z1.pack(side=RIGHT,padx=self.padx)
    #         if tab.plot.markers:
    #             self.outer_markerstyle_frame=Frame(self.plot_options_dialog.top,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
    #             self.outer_markerstyle_frame.pack(expand=True,fill=BOTH)
    #             self.markerstyle_label=Label(self.outer_markerstyle_frame,text='Markerstyle settings',bg=self.bg,fg=self.textcolor)
    #             self.markerstyle_label.pack()
    #
    #             self.markerstyle_frame=Frame(self.outer_markerstyle_frame,bg=self.bg,padx=self.padx,pady=15)
    #             self.markerstyle_frame.pack(fill=BOTH, expand=True)
    #             self.markerstyle_sample_frame=Frame(self.markerstyle_frame,bg=self.bg,padx=30,pady=0)
    #             self.markerstyle_sample_frame.pack(fill=BOTH, expand=True)
    #
    #             self.markerstyle_sample_label=Label(self.markerstyle_sample_frame,text='Sample: ',bg=self.bg,fg=self.textcolor)
    #             self.markerstyle_sample_label.pack(side=LEFT)
    #             self.markerstyle_sample_var=StringVar()
    #             sample_names=[]
    #             repeats=False
    #             max_len=0
    #             for sample in tab.samples:
    #                 if sample.name in sample_names:
    #                     repeats=True
    #                 else:
    #                     sample_names.append(sample.name)
    #                     max_len=np.max([max_len, len(sample.name)])
    #             if repeats:
    #                 sample_names=[]
    #                 for sample in tab.samples:
    #                     sample_names.append(sample.title+': '+sample.name)
    #                     max_len=np.max([max_len, len(sample_names[-1])])
    #             self.markerstyle_sample_var.set(sample_names[0])
    #             self.markerstyle_menu=OptionMenu(self.markerstyle_sample_frame, self.markerstyle_sample_var,*sample_names)
    #             self.markerstyle_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #             self.markerstyle_menu.pack(side=LEFT)
    #
    #             self.markerstyle_markerstyle_frame=Frame(self.markerstyle_frame,bg=self.bg,padx=44,pady=0)
    #             self.markerstyle_markerstyle_frame.pack(fill=BOTH, expand=True)
    #             self.markerstyle_sample_label=Label(self.markerstyle_markerstyle_frame,text='Style: ',bg=self.bg,fg=self.textcolor)
    #             self.markerstyle_sample_label.pack(side=LEFT)
    #             self.markerstyle_markerstyle_var=StringVar()
    #             markerstyle_names=['Circle','X','Diamond','Triangle']
    #
    #             self.markerstyle_markerstyle_var.set(markerstyle_names[0])
    #             self.markerstyle_menu=OptionMenu(self.markerstyle_markerstyle_frame, self.markerstyle_markerstyle_var,*markerstyle_names)
    #             self.markerstyle_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #             self.markerstyle_menu.pack(side=LEFT)
    #             self.markerstyle_button=Button(self.markerstyle_frame,text='Apply',  command=set_markerstyle,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #             self.markerstyle_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #             self.markerstyle_button.pack()
    #
    #
    #     def open_plot_settings(self, tab):
    #         #If the user already has dialogs open for editing the plot, close the extras to avoid confusion.
    #         self.close_plot_option_windows()
    #
    #         def select_tab():
    #             self.view_notebook.select(tab.top)
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         def set_markerstyle():
    #             tab.set_markerstyle(self.markerstyle_sample_var.get(), self.markerstyle_markerstyle_var.get())
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         def apply_x():
    #             self.view_notebook.select(tab.top)
    #
    #             try:
    #                 x1=float(self.left_zoom_entry.get())
    #                 x2=float(self.right_zoom_entry.get())
    #                 tab.adjust_x(x1,x2)
    #                 self.lift_widget(self.plot_settings_dialog.top)
    #             except:
    #                 self.lift_widget(self.plot_settings_dialog.top)
    #                 ErrorDialog(self, title='Invalid Zoom Range',label='Error: Invalid x limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
    #
    #         def apply_y():
    #             self.view_notebook.select(tab.top)
    #             try:
    #                 y1=float(self.left_zoom_entry2.get())
    #                 y2=float(self.right_zoom_entry2.get())
    #                 tab.adjust_y(y1,y2)
    #                 self.lift_widget(self.plot_settings_dialog.top)
    #             except Exception as e:
    #                 print(e)
    #                 self.lift_widget(self.plot_settings_dialog.top)
    #                 ErrorDialog(self, title='Invalid Zoom Range',label='Error! Invalid y limits: '+self.left_zoom_entry2.get()+', '+self.right_zoom_entry2.get())
    #
    #         def apply_z():
    #             self.view_notebook.select(tab.top)
    #
    #             try:
    #                 z1=float(self.left_zoom_entry_z.get())
    #                 z2=float(self.right_zoom_entry_z.get())
    #                 tab.adjust_z(z1,z2)
    #                 self.lift_widget(self.plot_settings_dialog.top)
    #             except Exception as e:
    #                 print(e)
    #                 self.lift_widget(self.plot_settings_dialog.top)
    #                 ErrorDialog(self, title='Invalid Zoom Range',label='Error: Invalid z limits: '+self.left_zoom_entry.get()+', '+self.right_zoom_entry.get())
    #
    #         def set_title():
    #             tab.set_title(self.title_entry.get())
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         def set_custom_color(custom_color):
    #             print('foo')
    #             print(self.custom_color)
    #             tab.set_color(self.color_sample_var.get(), custom_color)
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         def set_color():
    #             if self.color_color_var.get()=='Custom':
    #                 self.custom_color=None
    #                 try:
    #                     self.custom_color_dialog.top.destroy()
    #                 except:
    #                     pass
    #                 self.custom_color_dialog=CustomColorDialog(self,set_custom_color, self.custom_color)
    #                 self.lift_widget(self.custom_color_dialog.top)
    #             else:
    #                 tab.set_color(self.color_sample_var.get(), self.color_color_var.get())
    #
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         def set_linestyle():
    #             tab.set_linestyle(self.linestyle_sample_var.get(), self.linestyle_linestyle_var.get())
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         def set_markerstyle():
    #             tab.set_markerstyle(self.markerstyle_sample_var.get(), self.markerstyle_markerstyle_var.get())
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         tab.freeze() #You have to finish dealing with this before, say, opening another analysis box.
    #         buttons={
    #             'close':{}
    #         }
    #
    #         def set_legend():
    #             tab.set_legend_style(self.legend_legend_var.get())
    #             self.lift_widget(self.plot_settings_dialog.top)
    #
    #         self.plot_settings_dialog=VerticalScrolledDialog(self,'Plot Settings','',buttons=buttons,button_width=13, min_height=715, width=360)
    #         self.plot_settings_dialog.top.wm_geometry('380x756')
    # #         self.plot_settings_dialog.top.attributes('-topmost', True)
    #
    #         self.outer_title_frame=Frame(self.plot_settings_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
    #         self.outer_title_frame.pack(expand=True,fill=BOTH)
    #
    #         self.title_frame=Frame(self.outer_title_frame,bg=self.bg,padx=self.padx,pady=15)
    #         self.title_frame.pack(fill=BOTH, expand=True)
    #
    #         self.title_label=Label(self.title_frame,text='Plot title:',bg=self.bg,fg=self.textcolor)
    #         self.title_entry=Entry(self.title_frame, width=20, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.title_button=Button(self.title_frame,text='Apply',  command=set_title,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.title_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #         self.title_button.pack(side=RIGHT,padx=(10,20))
    #         self.title_entry.pack(side=RIGHT,padx=self.padx)
    #         self.title_label.pack(side=RIGHT,padx=self.padx)
    #
    #         self.outer_outer_zoom_frame=Frame(self.plot_settings_dialog.interior,bg=self.bg,padx=self.padx,pady=15, highlightthickness=1)
    #         self.outer_outer_zoom_frame.pack(expand=True,fill=BOTH)
    #
    #         self.zoom_title_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg)
    #         self.zoom_title_frame.pack(pady=(5,10))
    #         self.zoom_title_label=Label(self.zoom_title_frame,text='Adjust plot x and y limits:',bg=self.bg,fg=self.textcolor)
    #         self.zoom_title_label.pack(side=LEFT,pady=(0,4))
    #
    #         self.outer_zoom_frame=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
    #         self.outer_zoom_frame.pack(expand=True,fill=BOTH,pady=(0,10))
    #         self.zoom_frame=Frame(self.outer_zoom_frame,bg=self.bg,padx=self.padx)
    #         self.zoom_frame.pack()
    #
    #         self.zoom_label=Label(self.zoom_frame,text='x1:',bg=self.bg,fg=self.textcolor)
    #         self.left_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_label2=Label(self.zoom_frame,text='x2:',bg=self.bg,fg=self.textcolor)
    #         self.right_zoom_entry=Entry(self.zoom_frame, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_button=Button(self.zoom_frame,text='Apply',  command=apply_x,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.zoom_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #         self.zoom_button.pack(side=RIGHT,padx=(10,10))
    #         self.right_zoom_entry.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label2.pack(side=RIGHT,padx=self.padx)
    #         self.left_zoom_entry.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label.pack(side=RIGHT,padx=self.padx)
    #
    #
    #         self.outer_zoom_frame2=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
    #         self.outer_zoom_frame2.pack(expand=True,fill=BOTH,pady=(0,10))
    #         self.zoom_frame2=Frame(self.outer_zoom_frame2,bg=self.bg,padx=self.padx)
    #         self.zoom_frame2.pack()
    #         self.zoom_label3=Label(self.zoom_frame2,text='y1:',bg=self.bg,fg=self.textcolor)
    #         self.left_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_label4=Label(self.zoom_frame2,text='y2:',bg=self.bg,fg=self.textcolor)
    #         self.right_zoom_entry2=Entry(self.zoom_frame2, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #         self.zoom_button2=Button(self.zoom_frame2,text='Apply',  command=apply_y,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.zoom_button2.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #
    #         self.zoom_button2.pack(side=RIGHT,padx=(10,10))
    #         self.right_zoom_entry2.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label4.pack(side=RIGHT,padx=self.padx)
    #         self.left_zoom_entry2.pack(side=RIGHT,padx=self.padx)
    #         self.zoom_label3.pack(side=RIGHT,padx=self.padx)
    #
    #         if tab.plot.x_axis=='contour':
    #             self.outer_zoom_frame_z=Frame(self.outer_outer_zoom_frame,bg=self.bg,padx=self.padx)
    #             self.outer_zoom_frame_z.pack(expand=True,fill=BOTH,pady=(0,10))
    #             self.zoom_frame_z=Frame(self.outer_zoom_frame_z,bg=self.bg,padx=self.padx)
    #             self.zoom_frame_z.pack()
    #             self.zoom_label_z1=Label(self.zoom_frame_z,text='z1:',bg=self.bg,fg=self.textcolor)
    #             self.left_zoom_entry_z=Entry(self.zoom_frame_z, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #             self.zoom_label_z2=Label(self.zoom_frame_z,text='z2:',bg=self.bg,fg=self.textcolor)
    #             self.right_zoom_entry_z=Entry(self.zoom_frame_z, width=7, bd=self.bd,bg=self.entry_background,selectbackground=self.selectbackground,selectforeground=self.selectforeground)
    #             self.zoom_button_z=Button(self.zoom_frame_z,text='Apply',  command=apply_z,width=7, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #             self.zoom_button_z.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #
    #
    #
    #             self.zoom_button_z.pack(side=RIGHT,padx=(10,10))
    #             self.right_zoom_entry_z.pack(side=RIGHT,padx=self.padx)
    #             self.zoom_label_z2.pack(side=RIGHT,padx=self.padx)
    #             self.left_zoom_entry_z.pack(side=RIGHT,padx=self.padx)
    #             self.zoom_label_z1.pack(side=RIGHT,padx=self.padx)
    #
    #         self.outer_color_frame=Frame(self.plot_settings_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
    #         self.outer_color_frame.pack(expand=True,fill=BOTH)
    #         self.color_label=Label(self.outer_color_frame,text='Color settings',bg=self.bg,fg=self.textcolor)
    #         self.color_label.pack()
    #
    #         self.color_frame=Frame(self.outer_color_frame,bg=self.bg,padx=self.padx,pady=15)
    #         self.color_frame.pack(fill=BOTH, expand=True)
    #         self.color_sample_frame=Frame(self.color_frame,bg=self.bg,padx=30,pady=0)
    #         self.color_sample_frame.pack(fill=BOTH, expand=True)
    #
    #         self.color_sample_label=Label(self.color_sample_frame,text='Sample: ',bg=self.bg,fg=self.textcolor)
    #         self.color_sample_label.pack(side=LEFT)
    #         self.color_sample_var=StringVar()
    #         sample_names=[]
    #         repeats=False
    #         max_len=0
    #         for sample in tab.samples:
    #             if sample.name in sample_names:
    #                 repeats=True
    #             else:
    #                 sample_names.append(sample.name)
    #                 max_len=np.max([max_len, len(sample.name)])
    #         if repeats:
    #             sample_names=[]
    #             for sample in tab.samples:
    #                 sample_names.append(sample.title+': '+sample.name)
    #                 max_len=np.max([max_len, len(sample_names[-1])])
    #         self.color_sample_var.set(sample_names[0])
    #         self.color_menu=OptionMenu(self.color_sample_frame, self.color_sample_var,*sample_names)
    #         self.color_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #         self.color_menu.pack(side=LEFT)
    #
    #         self.color_color_frame=Frame(self.color_frame,bg=self.bg,padx=40,pady=0)
    #         self.color_color_frame.pack(fill=BOTH, expand=True)
    #         self.color_sample_label=Label(self.color_color_frame,text='Color: ',bg=self.bg,fg=self.textcolor)
    #         self.color_sample_label.pack(side=LEFT)
    #         self.color_color_var=StringVar()
    #         color_names=tab.plot.color_names
    #
    #         self.color_color_var.set(color_names[0])
    #         self.color_menu=OptionMenu(self.color_color_frame, self.color_color_var,*color_names)
    #         self.color_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #         self.color_menu.pack(side=LEFT)
    #         self.color_button=Button(self.color_frame,text='Apply',  command=set_color,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.color_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #         self.color_button.pack()
    #
    #         if tab.plot.lines_drawn:
    #             self.outer_linestyle_frame=Frame(self.plot_settings_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
    #             self.outer_linestyle_frame.pack(expand=True,fill=BOTH)
    #             self.linestyle_label=Label(self.outer_linestyle_frame,text='Linestyle settings',bg=self.bg,fg=self.textcolor)
    #             self.linestyle_label.pack()
    #
    #             self.linestyle_frame=Frame(self.outer_linestyle_frame,bg=self.bg,padx=self.padx,pady=15)
    #             self.linestyle_frame.pack(fill=BOTH, expand=True)
    #             self.linestyle_sample_frame=Frame(self.linestyle_frame,bg=self.bg,padx=30,pady=0)
    #             self.linestyle_sample_frame.pack(fill=BOTH, expand=True)
    #
    #             self.linestyle_sample_label=Label(self.linestyle_sample_frame,text='Sample: ',bg=self.bg,fg=self.textcolor)
    #             self.linestyle_sample_label.pack(side=LEFT)
    #             self.linestyle_sample_var=StringVar()
    #             sample_names=[]
    #             repeats=False
    #             max_len=0
    #             for sample in tab.samples:
    #                 if sample.name in sample_names:
    #                     repeats=True
    #                 else:
    #                     sample_names.append(sample.name)
    #                     max_len=np.max([max_len, len(sample.name)])
    #             if repeats:
    #                 sample_names=[]
    #                 for sample in tab.samples:
    #                     sample_names.append(sample.title+': '+sample.name)
    #                     max_len=np.max([max_len, len(sample_names[-1])])
    #             self.linestyle_sample_var.set(sample_names[0])
    #             self.linestyle_menu=OptionMenu(self.linestyle_sample_frame, self.linestyle_sample_var,*sample_names)
    #             self.linestyle_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #             self.linestyle_menu.pack(side=LEFT)
    #
    #             self.linestyle_linestyle_frame=Frame(self.linestyle_frame,bg=self.bg,padx=44,pady=0)
    #             self.linestyle_linestyle_frame.pack(fill=BOTH, expand=True)
    #             self.linestyle_sample_label=Label(self.linestyle_linestyle_frame,text='Style: ',bg=self.bg,fg=self.textcolor)
    #             self.linestyle_sample_label.pack(side=LEFT)
    #             self.linestyle_linestyle_var=StringVar()
    #             linestyle_names=['Solid','Dash','Dot','Dot-dash']
    #
    #             self.linestyle_linestyle_var.set(linestyle_names[0])
    #             self.linestyle_menu=OptionMenu(self.linestyle_linestyle_frame, self.linestyle_linestyle_var,*linestyle_names)
    #             self.linestyle_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #             self.linestyle_menu.pack(side=LEFT)
    #             self.linestyle_button=Button(self.linestyle_frame,text='Apply',  command=set_linestyle,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #             self.linestyle_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #             self.linestyle_button.pack()
    #
    #         if tab.plot.markers_drawn:
    #             self.outer_markerstyle_frame=Frame(self.plot_settings_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
    #             self.outer_markerstyle_frame.pack(expand=True,fill=BOTH)
    #             self.markerstyle_label=Label(self.outer_markerstyle_frame,text='Markerstyle settings',bg=self.bg,fg=self.textcolor)
    #             self.markerstyle_label.pack()
    #
    #             self.markerstyle_frame=Frame(self.outer_markerstyle_frame,bg=self.bg,padx=self.padx,pady=15)
    #             self.markerstyle_frame.pack(fill=BOTH, expand=True)
    #             self.markerstyle_sample_frame=Frame(self.markerstyle_frame,bg=self.bg,padx=30,pady=0)
    #             self.markerstyle_sample_frame.pack(fill=BOTH, expand=True)
    #
    #             self.markerstyle_sample_label=Label(self.markerstyle_sample_frame,text='Sample: ',bg=self.bg,fg=self.textcolor)
    #             self.markerstyle_sample_label.pack(side=LEFT)
    #             self.markerstyle_sample_var=StringVar()
    #             sample_names=[]
    #             repeats=False
    #             max_len=0
    #             for sample in tab.samples:
    #                 if sample.name in sample_names:
    #                     repeats=True
    #                 else:
    #                     sample_names.append(sample.name)
    #                     max_len=np.max([max_len, len(sample.name)])
    #             if repeats:
    #                 sample_names=[]
    #                 for sample in tab.samples:
    #                     sample_names.append(sample.title+': '+sample.name)
    #                     max_len=np.max([max_len, len(sample_names[-1])])
    #             self.markerstyle_sample_var.set(sample_names[0])
    #             self.markerstyle_menu=OptionMenu(self.markerstyle_sample_frame, self.markerstyle_sample_var,*sample_names)
    #             self.markerstyle_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #             self.markerstyle_menu.pack(side=LEFT)
    #
    #             self.markerstyle_markerstyle_frame=Frame(self.markerstyle_frame,bg=self.bg,padx=44,pady=0)
    #             self.markerstyle_markerstyle_frame.pack(fill=BOTH, expand=True)
    #             self.markerstyle_sample_label=Label(self.markerstyle_markerstyle_frame,text='Style: ',bg=self.bg,fg=self.textcolor)
    #             self.markerstyle_sample_label.pack(side=LEFT)
    #             self.markerstyle_markerstyle_var=StringVar()
    #             markerstyle_names=['Circle','X','Diamond','Triangle']
    #
    #             self.markerstyle_markerstyle_var.set(markerstyle_names[0])
    #             self.markerstyle_menu=OptionMenu(self.markerstyle_markerstyle_frame, self.markerstyle_markerstyle_var,*markerstyle_names)
    #             self.markerstyle_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #             self.markerstyle_menu.pack(side=LEFT)
    #             self.markerstyle_button=Button(self.markerstyle_frame,text='Apply',  command=set_markerstyle,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #             self.markerstyle_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #             self.markerstyle_button.pack()
    #
    #         self.outer_legend_frame=Frame(self.plot_settings_dialog.interior,bg=self.bg,padx=self.padx,pady=15,highlightthickness=1)
    #         self.outer_legend_frame.pack(expand=True,fill=BOTH)
    #
    #         self.legend_frame=Frame(self.outer_legend_frame,bg=self.bg,padx=self.padx,pady=15)
    #         self.legend_frame.pack(fill=BOTH, expand=True)
    #
    #         self.legend_legend_frame=Frame(self.legend_frame,bg=self.bg,padx=20,pady=0)
    #         self.legend_legend_frame.pack(fill=BOTH, expand=True)
    #         self.legend_sample_label=Label(self.legend_legend_frame,text='Legend style: ',bg=self.bg,fg=self.textcolor)
    #         self.legend_sample_label.pack(side=LEFT)
    #         self.legend_legend_var=StringVar()
    #         legend_names=['Full list','Gradient']
    #
    #         self.legend_legend_var.set(legend_names[0])
    #         self.legend_menu=OptionMenu(self.legend_legend_frame, self.legend_legend_var,*legend_names)
    #         self.legend_menu.configure(width=max_len,highlightbackground=self.highlightbackgroundcolor)
    #         self.legend_menu.pack(side=LEFT)
    #         self.legend_button=Button(self.legend_legend_frame,text='Apply',  command=set_legend,width=6, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,bd=self.bd)
    #         self.legend_button.config(fg=self.buttontextcolor,highlightbackground=self.highlightbackgroundcolor,bg=self.buttonbackgroundcolor)
    #         self.legend_button.pack(side=LEFT, padx=(5,5),pady=(5,3))

    def lift_widget(self, widget):
        widget.focus_set()
        widget.lift()

    def thread_lift_widget(self, widget):
        thread = Thread(target=self.lift_widget, args=(widget,))
        thread.start()

    def open_analysis_tools(self, tab):

        # tab.set_exclude_artifacts(True)
        def calculate():
            self.view_notebook.select(tab.top)
            artifact_warning = False

            if self.analyze_var.get() == 'slope':
                left, right, slopes, artifact_warning = tab.calculate_slopes(self.left_slope_entry.get(),
                                                                             self.right_slope_entry.get())
                update_entries(left, right)
                populate_listbox(slopes)
                update_plot_menu(['e', 'i', 'g', 'e,i', 'theta'])

            elif self.analyze_var.get() == 'band depth':
                left, right, depths, artifact_warning = tab.calculate_band_depths(self.left_slope_entry.get(),
                                                                                  self.right_slope_entry.get(),
                                                                                  self.neg_depth.get(),
                                                                                  self.use_delta.get())
                update_entries(left, right)
                populate_listbox(depths)
                update_plot_menu(['e', 'i', 'g', 'e,i', 'theta'])

            elif self.analyze_var.get() == 'band center':
                left, right, centers, artifact_warning = tab.calculate_band_centers(self.left_slope_entry.get(),
                                                                                    self.right_slope_entry.get(),
                                                                                    self.use_max_for_centers.get(),
                                                                                    self.use_delta.get())
                update_entries(left, right)
                populate_listbox(centers)
                update_plot_menu(['e', 'i', 'g', 'e,i', 'theta'])

            elif self.analyze_var.get() == 'reflectance':
                left, right, reflectance, artifact_warning = tab.calculate_avg_reflectance(self.left_slope_entry.get(),
                                                                                           self.right_slope_entry.get())
                update_entries(left, right)
                populate_listbox(reflectance)
                update_plot_menu(['e', 'i', 'g', 'e,i', 'theta'])

            elif self.analyze_var.get() == 'reciprocity':
                left, right, reciprocity, artifact_warning = tab.calculate_reciprocity(self.left_slope_entry.get(),
                                                                                       self.right_slope_entry.get())
                update_entries(left, right)
                populate_listbox(reciprocity)
                update_plot_menu(['e', 'i', 'g', 'e,i'])

            elif self.analyze_var.get() == 'difference':
                left, right, error, artifact_warning = tab.calculate_error(self.left_slope_entry.get(),
                                                                           self.right_slope_entry.get(),
                                                                           self.abs_val.get())
                # Tab validates left and right values. If they are no good, put in min and max wavelengths available.
                update_entries(left, right)
                populate_listbox(error)
                update_plot_menu([u'\u03bb', 'e,i'])

            if artifact_warning:
                dialog = ErrorDialog(self, 'Warning',
                                     'Warning: Excluding data potentially\ninfluenced by artifacts from 1000-1400 nm.')

            self.analysis_dialog.min_height = 1000
            self.analysis_dialog.update()

        def update_plot_menu(plot_options):
            self.plot_slope_var.set(plot_options[0])
            self.plot_slope_menu['menu'].delete(0, 'end')

            # Insert list of new options (tk._setit hooks them up to var)
            max_len = len(plot_options[0])
            for option in plot_options:
                max_len = np.max([max_len, len(option)])
                self.plot_slope_menu['menu'].add_command(label=option, command=tk._setit(self.plot_slope_var, option))
            self.plot_slope_menu.configure(width=max_len)

        def update_entries(left, right):
            self.left_slope_entry.delete(0, 'end')
            self.left_slope_entry.insert(0, str(left))
            self.right_slope_entry.delete(0, 'end')
            self.right_slope_entry.insert(0, str(right))

        def populate_listbox(results):
            if len(results) > 0:
                self.slope_results_frame.pack(fill=BOTH, expand=True, pady=(10, 10))
                try:
                    self.slopes_listbox.delete(0, 'end')
                except:
                    self.slopes_listbox = ScrollableListbox(self.slope_results_frame, self.bg, self.entry_background,
                                                            self.listboxhighlightcolor, selectmode=EXTENDED)
                    self.slopes_listbox.configure(height=8)
                for result in results:
                    self.slopes_listbox.insert('end', result)
                self.slopes_listbox.pack(fill=BOTH, expand=True)
                self.plot_slope_button.configure(state=NORMAL)

        def plot():
            if self.analyze_var.get() == 'slope':
                tab.plot_slopes(self.plot_slope_var.get())
            elif self.analyze_var.get() == 'band depth':
                tab.plot_band_depths(self.plot_slope_var.get())
            elif self.analyze_var.get() == 'band center':
                tab.plot_band_centers(self.plot_slope_var.get())
            elif self.analyze_var.get() == 'reflectance':
                tab.plot_avg_reflectance(self.plot_slope_var.get())
            elif self.analyze_var.get() == 'reciprocity':
                tab.plot_reciprocity(self.plot_slope_var.get())
            elif self.analyze_var.get() == 'difference':
                new = tab.plot_error(self.plot_slope_var.get())

            if self.plot_slope_var.get() == '\u03bb':
                x1 = float(self.left_slope_entry.get())
                x2 = float(self.right_slope_entry.get())
                new.adjust_x(x1, x2)

            self.thread_lift_widget(self.analysis_dialog.top)

        def normalize():
            select_tab()

            try:
                self.slopes_listbox.delete(0, 'end')
                self.plot_slope_button.configure(state='disabled')
            except:
                pass
            tab.normalize(self.normalize_entry.get())
            thread = Thread(target=self.lift_widget, args=(self.analysis_dialog.top,))
            thread.start()

        def offset():
            tab.offset(self.offset_sample_var.get(), self.offset_entry.get())
            thread = Thread(target=self.lift_widget, args=(self.analysis_dialog.top,))
            thread.start()

        def apply_x():
            self.view_notebook.select(tab.top)

            try:
                x1 = float(self.left_zoom_entry.get())
                x2 = float(self.right_zoom_entry.get())
                tab.adjust_x(x1, x2)
                self.lift_widget(self.analysis_dialog.top)
            except:
                self.lift_widget(self.analysis_dialog.top)
                ErrorDialog(self, title='Invalid Zoom Range',
                            label='Error! Invalid x limits: ' + self.left_zoom_entry.get() + ', ' + self.right_zoom_entry.get())

        def apply_y():
            self.view_notebook.select(tab.top)
            try:
                y1 = float(self.left_zoom_entry2.get())
                y2 = float(self.right_zoom_entry2.get())
                tab.adjust_y(y1, y2)
                self.lift_widget(self.analysis_dialog.top)
            except:
                self.lift_widget(self.analysis_dialog.top)
                ErrorDialog(self, title='Invalid Zoom Range',
                            label='Error! Invalid y limits: ' + self.left_zoom_entry2.get() + ', ' + self.right_zoom_entry2.get())

        def uncheck_exclude_artifacts():
            self.exclude_artifacts.set(0)
            self.exclude_artifacts_check.deselect()
            self.lift_widget(self.analysis_dialog.top)

        def disable_plot(analyze_var='None'):
            try:
                self.slopes_listbox.delete(0, 'end')
            except:
                pass
            self.plot_slope_button.configure(state='disabled')

            if analyze_var == 'difference':
                self.neg_depth_check.pack_forget()
                self.use_max_for_centers_check.pack_forget()
                self.use_delta_check.pack_forget()
                self.abs_val_check.pack()
                self.extra_analysis_check_frame.pack()

            elif analyze_var == 'band center':
                self.neg_depth_check.pack_forget()
                self.abs_val_check.pack_forget()
                self.use_delta_check.pack_forget()
                self.use_max_for_centers_check.pack()
                self.use_delta_check.pack()
                self.extra_analysis_check_frame.pack()

            elif analyze_var == 'band depth':
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

        def calculate_photometric_variability():

            photo_var = tab.calculate_photometric_variability(self.right_photo_var_entry.get(),
                                                              self.left_photo_var_entry.get())
            try:
                self.photo_var_listbox.delete(0, 'end')
            except:
                self.photo_var_listbox = ScrollableListbox(self.photo_var_results_frame, self.bg, self.entry_background,
                                                           self.listboxhighlightcolor, selectmode=EXTENDED)
            for var in photo_var:
                self.photo_var_listbox.insert('end', var)
            self.photo_var_listbox.pack(fill=BOTH, expand=True)

        def select_tab():
            self.view_notebook.select(tab.top)
            self.lift_widget(self.analysis_dialog.top)

        def lift():
            self.thread_lift_widget(self.analysis_dialog.top)

        tab.freeze()  # You have to finish dealing with this before, say, opening another analysis box.
        buttons = {
            'reset': {
                select_tab: [],
                tab.reset: [],
                uncheck_exclude_artifacts: [],
                disable_plot: [],
                lift: []
            },
            'close': {}
        }

        # If the user already has analysis tools or a plot editing dialog open, close the extra to avoid confusion.
        self.close_plot_option_windows()

        self.analysis_dialog = VerticalScrolledDialog(self, 'Analyze Data', '', buttons=buttons, button_width=13)
        #         self.analysis_dialog.top.attributes('-topmost', True)

        self.outer_normalize_frame = Frame(self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15,
                                           highlightthickness=1)
        self.outer_normalize_frame.pack(expand=True, fill=BOTH)
        self.slope_title_label = Label(self.outer_normalize_frame, text='Normalize:', bg=self.bg, fg=self.textcolor)
        self.slope_title_label.pack()
        self.normalize_frame = Frame(self.outer_normalize_frame, bg=self.bg, padx=self.padx, pady=15)
        self.normalize_frame.pack()

        self.normalize_label = Label(self.normalize_frame, text='Wavelength (nm):', bg=self.bg, fg=self.textcolor)
        self.normalize_entry = Entry(self.normalize_frame, width=7, bd=self.bd, bg=self.entry_background,
                                     selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.normalize_button = Button(self.normalize_frame, text='Apply', command=normalize, width=6,
                                       fg=self.buttontextcolor, bg=self.buttonbackgroundcolor, bd=self.bd)
        self.normalize_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                     bg=self.buttonbackgroundcolor)
        self.normalize_button.pack(side=RIGHT, padx=(10, 10))
        self.normalize_entry.pack(side=RIGHT, padx=self.padx)
        self.normalize_label.pack(side=RIGHT, padx=self.padx)

        self.outer_offset_frame = Frame(self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15,
                                        highlightthickness=1)
        self.outer_offset_frame.pack(expand=True, fill=BOTH)
        self.slope_title_label = Label(self.outer_offset_frame, text='Add offset to sample:', bg=self.bg,
                                       fg=self.textcolor)
        self.slope_title_label.pack(pady=(0, 15))
        self.offset_sample_frame = Frame(self.outer_offset_frame, bg=self.bg, padx=self.padx, pady=self.pady)
        self.offset_sample_frame.pack()
        self.offset_sample_label = Label(self.offset_sample_frame, text='Sample: ', bg=self.bg, fg=self.textcolor)
        self.offset_sample_label.pack(side=LEFT)
        self.offset_sample_var = StringVar()
        sample_names = []
        repeats = False
        max_len = 0
        for sample in tab.samples:
            if sample.name in sample_names:
                repeats = True
            else:
                sample_names.append(sample.name)
                max_len = np.max([max_len, len(sample.name)])
        if repeats:
            sample_names = []
            for sample in tab.samples:
                sample_names.append(sample.title + ': ' + sample.name)
                max_len = np.max([max_len, len(sample_names[-1])])
        self.offset_sample_var.set(sample_names[0])
        self.offset_menu = OptionMenu(self.offset_sample_frame, self.offset_sample_var, *sample_names)
        self.offset_menu.configure(width=max_len, highlightbackground=self.highlightbackgroundcolor)
        self.offset_menu.pack(side=LEFT)
        self.offset_frame = Frame(self.outer_offset_frame, bg=self.bg, padx=self.padx, pady=15)
        self.offset_frame.pack()
        self.offset_label = Label(self.offset_frame, text='Offset:', bg=self.bg, fg=self.textcolor)
        self.offset_entry = Entry(self.offset_frame, width=7, bd=self.bd, bg=self.entry_background,
                                  selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.offset_button = Button(self.offset_frame, text='Apply', command=offset, width=6, fg=self.buttontextcolor,
                                    bg=self.buttonbackgroundcolor, bd=self.bd)
        self.offset_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                  bg=self.buttonbackgroundcolor)
        self.offset_button.pack(side=RIGHT, padx=(10, 10))
        self.offset_entry.pack(side=RIGHT, padx=self.padx)
        self.offset_label.pack(side=RIGHT, padx=self.padx)

        self.outer_outer_zoom_frame = Frame(self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15,
                                            highlightthickness=1)
        self.outer_outer_zoom_frame.pack(expand=True, fill=BOTH)

        self.zoom_title_frame = Frame(self.outer_outer_zoom_frame, bg=self.bg)
        self.zoom_title_frame.pack(pady=(5, 10))
        self.zoom_title_label = Label(self.zoom_title_frame, text='Adjust plot x and y limits:', bg=self.bg,
                                      fg=self.textcolor)
        self.zoom_title_label.pack(side=LEFT, pady=(0, 4))

        self.outer_zoom_frame = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
        self.outer_zoom_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        self.zoom_frame = Frame(self.outer_zoom_frame, bg=self.bg, padx=self.padx)
        self.zoom_frame.pack()

        self.zoom_label = Label(self.zoom_frame, text='x1:', bg=self.bg, fg=self.textcolor)
        self.left_zoom_entry = Entry(self.zoom_frame, width=7, bd=self.bd, bg=self.entry_background,
                                     selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.zoom_label2 = Label(self.zoom_frame, text='x2:', bg=self.bg, fg=self.textcolor)
        self.right_zoom_entry = Entry(self.zoom_frame, width=7, bd=self.bd, bg=self.entry_background,
                                      selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.zoom_button = Button(self.zoom_frame, text='Apply', command=apply_x, width=7, fg=self.buttontextcolor,
                                  bg=self.buttonbackgroundcolor, bd=self.bd)
        self.zoom_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                bg=self.buttonbackgroundcolor)
        self.zoom_button.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry.pack(side=RIGHT, padx=self.padx)
        self.zoom_label2.pack(side=RIGHT, padx=self.padx)
        self.left_zoom_entry.pack(side=RIGHT, padx=self.padx)
        self.zoom_label.pack(side=RIGHT, padx=self.padx)

        self.outer_zoom_frame2 = Frame(self.outer_outer_zoom_frame, bg=self.bg, padx=self.padx)
        self.outer_zoom_frame2.pack(expand=True, fill=BOTH, pady=(0, 10))
        self.zoom_frame2 = Frame(self.outer_zoom_frame2, bg=self.bg, padx=self.padx)
        self.zoom_frame2.pack()
        self.zoom_label3 = Label(self.zoom_frame2, text='y1:', bg=self.bg, fg=self.textcolor)
        self.left_zoom_entry2 = Entry(self.zoom_frame2, width=7, bd=self.bd, bg=self.entry_background,
                                      selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.zoom_label4 = Label(self.zoom_frame2, text='y2:', bg=self.bg, fg=self.textcolor)
        self.right_zoom_entry2 = Entry(self.zoom_frame2, width=7, bd=self.bd, bg=self.entry_background,
                                       selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.zoom_button2 = Button(self.zoom_frame2, text='Apply', command=apply_y, width=7, fg=self.buttontextcolor,
                                   bg=self.buttonbackgroundcolor, bd=self.bd)
        self.zoom_button2.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                 bg=self.buttonbackgroundcolor)

        self.zoom_button2.pack(side=RIGHT, padx=(10, 10))
        self.right_zoom_entry2.pack(side=RIGHT, padx=self.padx)
        self.zoom_label4.pack(side=RIGHT, padx=self.padx)
        self.left_zoom_entry2.pack(side=RIGHT, padx=self.padx)
        self.zoom_label3.pack(side=RIGHT, padx=self.padx)

        self.outer_outer_slope_frame = Frame(self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15,
                                             highlightthickness=1)
        self.outer_outer_slope_frame.pack(expand=True, fill=BOTH)

        self.outer_slope_frame = Frame(self.outer_outer_slope_frame, bg=self.bg, padx=self.padx)
        self.outer_slope_frame.pack(expand=True, fill=BOTH, pady=(0, 10))
        self.slope_title_frame = Frame(self.outer_slope_frame, bg=self.bg)
        self.slope_title_frame.pack(pady=(5, 5))
        self.slope_title_label = Label(self.slope_title_frame, text='Analyze ', bg=self.bg, fg=self.textcolor)
        self.slope_title_label.pack(side=LEFT, pady=(0, 4))
        self.analyze_var = StringVar()
        self.analyze_var.set('slope')
        self.analyze_menu = OptionMenu(self.slope_title_frame, self.analyze_var, 'slope', 'band depth', 'band center',
                                       'reflectance', 'reciprocity', 'difference', command=disable_plot)
        self.analyze_menu.configure(width=10, highlightbackground=self.highlightbackgroundcolor)
        self.analyze_menu.pack(side=LEFT)

        # We'll put checkboxes for additional options into this frame at the time the user selects a given option (e.g. select 'difference' from menu, add option to calculate differences based on absolute value
        self.extra_analysis_check_frame = Frame(self.outer_slope_frame, bg=self.bg, padx=self.padx)
        self.extra_analysis_check_frame.pack()
        self.abs_val = IntVar()
        # Note that we are not packing this checkbutton yet.
        self.abs_val_check = Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg, fg=self.textcolor,
                                         text=' Use absolute values for average differences', bg=self.bg,
                                         pady=self.pady, highlightthickness=0, variable=self.abs_val)

        self.use_max_for_centers = IntVar()
        self.use_max_for_centers_check = Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,
                                                     fg=self.textcolor,
                                                     text=' If band max is more prominent than\nband min, use to find center.',
                                                     bg=self.bg, pady=self.pady, highlightthickness=0,
                                                     variable=self.use_max_for_centers)
        self.use_max_for_centers_check.select()

        self.use_delta = IntVar()
        self.use_delta_check = Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,
                                           fg=self.textcolor,
                                           text=u' Center at max \u0394' + 'R from continuum  \nrather than spectral min/max. ',
                                           bg=self.bg, pady=self.pady, highlightthickness=0, variable=self.use_delta)
        self.use_delta_check.select()

        self.neg_depth = IntVar()
        self.neg_depth_check = Checkbutton(self.extra_analysis_check_frame, selectcolor=self.check_bg,
                                           fg=self.textcolor,
                                           text=' If band max is more prominent than \nband min, report negative depth.',
                                           bg=self.bg, pady=self.pady, highlightthickness=0, variable=self.neg_depth)
        self.neg_depth_check.select()

        self.slope_frame = Frame(self.outer_slope_frame, bg=self.bg, padx=self.padx, highlightthickness=0)
        self.slope_frame.pack(pady=(15, 0))

        self.slope_label = Label(self.slope_frame, text='x1:', bg=self.bg, fg=self.textcolor)
        self.left_slope_entry = Entry(self.slope_frame, width=7, bd=self.bd, bg=self.entry_background,
                                      selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.slope_label_2 = Label(self.slope_frame, text='x2:', bg=self.bg, fg=self.textcolor)
        self.right_slope_entry = Entry(self.slope_frame, width=7, bd=self.bd, bg=self.entry_background,
                                       selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        self.slope_button = Button(self.slope_frame, text='Calculate', command=calculate, width=7,
                                   fg=self.buttontextcolor, bg=self.buttonbackgroundcolor, bd=self.bd)
        self.slope_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                 bg=self.buttonbackgroundcolor)

        self.slope_button.pack(side=RIGHT, padx=(10, 10))
        self.right_slope_entry.pack(side=RIGHT, padx=self.padx)
        self.slope_label_2.pack(side=RIGHT, padx=self.padx)
        self.left_slope_entry.pack(side=RIGHT, padx=self.padx)
        self.slope_label.pack(side=RIGHT, padx=self.padx)
        self.slope_results_frame = Frame(self.outer_slope_frame, bg=self.bg)
        self.slope_results_frame.pack(fill=BOTH,
                                      expand=True)  # We'll put a listbox with slope info in here later after calculating.

        self.outer_plot_slope_frame = Frame(self.outer_outer_slope_frame, bg=self.bg, padx=self.padx, pady=10)
        self.outer_plot_slope_frame.pack(expand=True, fill=BOTH)
        self.plot_slope_frame = Frame(self.outer_plot_slope_frame, bg=self.bg, padx=self.padx)
        self.plot_slope_frame.pack(side=RIGHT)
        self.plot_slope_label = Label(self.plot_slope_frame, text='Plot as a function of', bg=self.bg,
                                      fg=self.textcolor)
        self.plot_slope_var = StringVar()
        self.plot_slope_var.set('e')
        self.plot_slope_menu = OptionMenu(self.plot_slope_frame, self.plot_slope_var, 'e', 'i', 'g', 'e,i', 'theta')
        self.plot_slope_menu.configure(width=2, highlightbackground=self.highlightbackgroundcolor)
        self.plot_slope_button = Button(self.plot_slope_frame, text='Plot', command=plot, width=7,
                                        fg=self.buttontextcolor, bg=self.buttonbackgroundcolor, bd=self.bd)
        self.plot_slope_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                      bg=self.buttonbackgroundcolor, state=DISABLED)
        self.plot_slope_button.pack(side=RIGHT, padx=(10, 10))
        self.plot_slope_menu.pack(side=RIGHT, padx=self.padx)
        self.plot_slope_label.pack(side=RIGHT, padx=self.padx)

        self.exclude_artifacts_frame = Frame(self.analysis_dialog.interior, bg=self.bg, padx=self.padx, pady=15,
                                             highlightthickness=1)
        self.exclude_artifacts_frame.pack(fill=BOTH, expand=True)
        self.exclude_artifacts = IntVar()
        self.exclude_artifacts_check = Checkbutton(self.exclude_artifacts_frame, selectcolor=self.check_bg,
                                                   fg=self.textcolor,
                                                   text=' Exclude data susceptible to artifacts\n (high g, 1000-1400 nm)  ',
                                                   bg=self.bg, pady=self.pady, highlightthickness=0,
                                                   variable=self.exclude_artifacts,
                                                   command=lambda x='foo',: tab.set_exclude_artifacts(
                                                       self.exclude_artifacts.get()))
        self.exclude_artifacts_check.pack()
        if tab.exclude_artifacts:
            self.exclude_artifacts_check.select()

        self.analysis_dialog.interior.configure(highlightthickness=1, highlightcolor='white')

    def close_plot_option_windows(self):
        try:
            self.analysis_dialog.top.destroy()
        except:
            pass
        try:
            self.edit_plot_dialog.top.destroy()
        except:
            pass
        try:
            self.plot_options_dialog.top.destroy()
        except:
            pass
        try:
            self.plot_settings_dialog.top.destroy()
        except:
            pass

    # This gets called when the user clicks 'Edit plot' from the right-click menu on a plot.
    # Pops up a scrollable listbox with sample options.
    def ask_plot_samples(self, tab, existing_sample_indices, sample_options, existing_geoms, current_title):
        def config_tol_entry():
            return  # Decided againsta having the tolerance entry disabled if you don't have exclude specular angles checked.
            if self.exclude_specular.get():
                self.spec_tolerance_entry.configure(state=NORMAL)
            else:
                self.spec_tolerance_entry.configure(state=DISABLED)

        def select_tab():
            self.view_notebook.select(tab.top)

        buttons = {
            'ok': {
                select_tab: [],
                # The lambda sends a list of the currently selected samples back to the tab along with the new title and selected incidence/emission angles
                lambda: tab.set_samples(
                    list(map(lambda y: sample_options[y], self.plot_samples_listbox.curselection())),
                    self.new_plot_title_entry.get(),
                    *check_angle_lists(self.i_entry.get(), self.e_entry.get(), self.az_entry.get()),
                    self.exclude_specular.get(), self.spec_tolerance_entry.get()): []
            }
        }

        def check_angle_lists(incidences, emissions, azimuths):
            def check_list(angle_list):
                invalid_list = []
                angle_list = angle_list.split(',')
                if 'None' in angle_list or 'none' in angle_list:
                    while 'None' in angle_list: angle_list.remove('None')
                    while 'none' in angle_list: angle_list.remove('none')
                    angle_list.append(None)
                if angle_list == ['']: angle_list = []
                for n, angle in enumerate(angle_list):
                    if angle != None:
                        try:
                            angle_list[n] = int(angle)
                        except:
                            invalid_list.append(angle)

                return angle_list, invalid_list

            incidences, invalid_incidences = check_list(incidences)
            emissions, invalid_emissions = check_list(emissions)
            azimuths, invalid_azimuths = check_list(azimuths)
            if invalid_incidences != [] or invalid_emissions != [] or invalid_azimuths != []:
                error_string = 'Warning! Not all angles entered are valid.\n'
                if invalid_incidences != []: error_string += '\nInvalid incidences: ' + str(invalid_incidences)
                if invalid_emissions != []: error_string += '\nInvalid emissions: ' + str(invalid_emissions)
                if invalid_azimuths != []: error_string += '\nInvalid azimuths: ' + str(invalid_azimuths)
                ErrorDialog(self, 'Warning!', error_string)

            return incidences, emissions, azimuths

        self.close_plot_option_windows()

        self.edit_plot_dialog = Dialog(self, 'Edit Plot', '\nPlot title:', buttons=buttons)
        self.new_plot_title_entry = Entry(self.edit_plot_dialog.top, width=20, bd=self.bd, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground)
        self.new_plot_title_entry.insert(0, current_title)
        self.new_plot_title_entry.pack()

        sample_label = Label(self.edit_plot_dialog.top, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                             text='\nSamples:')
        sample_label.pack(pady=(0, 10))
        self.plot_samples_listbox = ScrollableListbox(self.edit_plot_dialog.top, self.bg, self.entry_background,
                                                      self.listboxhighlightcolor, selectmode=EXTENDED)

        self.geom_label = Label(self.edit_plot_dialog.top, padx=self.padx, pady=self.pady, bg=self.bg,
                                fg=self.textcolor,
                                text='\nEnter incidence and emission angles to plot,\nor leave blank to plot all:\n')
        self.geom_label.pack()
        self.geom_frame = Frame(self.edit_plot_dialog.top)
        self.geom_frame.pack(padx=(20, 20), pady=(0, 10))
        self.i_label = Label(self.geom_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text='i: ')
        self.i_label.pack(side=LEFT)
        self.i_entry = Entry(self.geom_frame, width=8, bd=self.bd, bg=self.entry_background,
                             selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        for i, incidence in enumerate(existing_geoms['i']):
            if i == 0:
                self.i_entry.insert(0, str(incidence))
            else:
                self.i_entry.insert('end', ',' + str(incidence))

        self.i_entry.pack(side=LEFT)

        self.e_label = Label(self.geom_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                             text='    e: ')
        self.e_label.pack(side=LEFT)
        self.e_entry = Entry(self.geom_frame, width=8, bd=self.bd, bg=self.entry_background,
                             selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        for i, emission in enumerate(existing_geoms['e']):
            if i == 0:
                self.e_entry.insert(0, str(emission))
            else:
                self.e_entry.insert('end', ',' + str(emission))
        self.e_entry.pack(side=LEFT)

        self.az_label = Label(self.geom_frame, padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor,
                              text='    az: ')
        self.az_label.pack(side=LEFT)
        self.az_entry = Entry(self.geom_frame, width=8, bd=self.bd, bg=self.entry_background,
                              selectbackground=self.selectbackground, selectforeground=self.selectforeground)
        for i, azimuth in enumerate(existing_geoms['az']):
            if i == 0:
                self.az_entry.insert(0, str(azimuth))
            else:
                self.az_entry.insert('end', ',' + str(azimuth))
        self.az_entry.pack(side=LEFT)
        print('packed')

        self.exclude_specular_frame = Frame(self.edit_plot_dialog.top, bg=self.bg, padx=self.padx, pady=self.pady)
        self.exclude_specular_frame.pack()
        self.exclude_specular = IntVar()
        self.exclude_specular_check = Checkbutton(self.exclude_specular_frame, selectcolor=self.check_bg,
                                                  fg=self.textcolor, text='  Exclude specular angles (+/-', bg=self.bg,
                                                  pady=self.pady, highlightthickness=0, command=config_tol_entry,
                                                  variable=self.exclude_specular)
        self.exclude_specular_check.pack(side=LEFT)

        self.spec_tolerance_entry = Entry(self.exclude_specular_frame, width=4, bd=self.bd, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground)

        self.spec_tolerance_entry.pack(side=LEFT)
        self.spec_tolerance_label = Label(self.exclude_specular_frame, padx=self.padx, pady=self.pady, bg=self.bg,
                                          fg=self.textcolor, text=u'\u00B0)')
        self.spec_tolerance_label.pack(side=LEFT)

        if tab.exclude_specular:
            self.exclude_specular_check.select()
            self.spec_tolerance_entry.insert(0, tab.specularity_tolerance)

        sample_files = []
        for option in sample_options:
            self.plot_samples_listbox.insert(END, option)

        for i in existing_sample_indices:
            self.plot_samples_listbox.select_set(i)
        self.plot_samples_listbox.config(height=8)

    def reset_plot_data(self):
        self.plotter = Plotter(self, self.get_dpi(), [self.global_config_loc + 'color_config.mplstyle',
                                                      self.global_config_loc + 'size_config.mplstyle'])
        for i, tab in enumerate(self.view_notebook.tabs()):
            if i == 0:
                continue
            else:
                self.view_notebook.forget(tab)

    def plot(self):
        filename = self.plot_input_dir_entry.get()
        if self.opsys == 'Windows' or self.plot_remote.get(): filename = filename.replace('\\', '/')

        if self.plot_remote.get():
            self.queue.insert(0, {self.plot: []})
            self.queue.insert(1, {self.actually_plot: [self.spec_share_loc + 'plot_temp.csv']})
            self.spec_commander.transfer_data(filename, 'spec_share_loc', 'plot_temp.csv')
            data_handler = DataHandler(self, source=filename, temp_destination=self.spec_share_loc + 'plot_temp.csv',
                                       final_destination=self.spec_share_loc + 'plot_temp.csv')
        else:
            if os.path.exists(filename):
                self.actually_plot(filename)
            else:

                dialog = ErrorDialog(self, title='Error: File not found',
                                     label='Error: File not found.\n\n' + filename + '\n\ndoes not exist.')
                return False

    def actually_plot(self, filename):
        if len(self.queue) > 0:
            print('There is a queue here if and only if we are transferring data from a remote location.')
            self.complete_queue_item()
        title = self.plot_title_entry.get()
        caption = ''  # self.plot_caption_entry.get()

        try:
            self.plot_input_file = self.plot_input_dir_entry.get()
            self.plot_title = self.plot_title_entry.get()
            if self.plot_remote.get():
                self.plot_local_remote = 'remote'
            elif self.plot_local.get():
                self.plot_local_remote = 'local'

            with open(self.local_config_loc + 'plot_config.txt', 'w') as plot_config:
                plot_config.write(self.plot_local_remote + '\n')
                plot_config.write(self.plot_input_file + '\n')
                plot_config.write(self.plot_title + '\n')

            self.plot_top.destroy()

            if self.plotter.controller.plot_local_remote == 'remote':
                self.plotter.plot_spectra(title, filename, caption, exclude_wr=False, draw=False)
                self.plotter.tabs[-1].ask_which_samples()
            else:
                self.plotter.plot_spectra(title, filename, caption, exclude_wr=False, draw=True)
                self.plotter.tabs[-1].ask_which_samples()

            self.goniometer_view.flip()

            last = len(self.view_notebook.tabs()) - 1

            self.view_notebook.select(last)
            if self.plotter.save_dir == None:  # If the user hasn't specified a folder where they want to save plots yet, set the default folder to be the same one they got the data from. Otherwise, leave it as is.
                if self.opsys == 'Windows':
                    self.plotter.save_dir = '\\'.join(filename.split('\\')[0:-1])
                else:
                    self.plotter.save_dir = '/'.join(filename.split('/')[0:-1])

        except Exception as e:
            print(e)

            dialog = Dialog(self, 'Plotting Error',
                            'Error: Plotting failed.\n\nDoes file exist? Is data formatted correctly?\nIf plotting a remote file, is the server accessible?',
                            {'ok': {}})
            raise e

    def auto_cycle_check(self):
        if self.auto.get():
            light_end_label.config(fg='black')
            detector_end_label.config(fg='black')
            light_increment_label.config(fg='black')
            detector_increment_label.config(fg='black')
            light_end_entry.config(bd=3)
            detector_end_entry.config(bd=3)
            light_increment_entry.config(bd=3)
            detector_increment_entry.config(bd=3)
        else:
            light_end_label.config(fg='lightgray')
            detector_end_label.config(fg='lightgray')
            light_increment_label.config(fg='lightgray')
            detector_increment_label.config(fg='lightgray')
            light_end_entry.config(bd=1)
            detector_end_entry.config(bd=1)
            light_increment_entry.config(bd=1)
            detector_increment_entry.config(bd=1)

        if keypress_event.keycode == 111:
            if len(user_cmds) > user_cmd_index + 1 and len(user_cmds) > 0:
                user_cmd_index = user_cmd_index + 1
                last = user_cmds[user_cmd_index]
                self.console_entry.delete(0, 'end')
                self.console_entry.insert(0, last)

        elif keypress_event.keycode == 116:
            if user_cmd_index > 0:
                user_cmd_index = self.user_cmd_index - 1
                next = selfuser_cmds[user_cmd_index]
                self.console_entry.delete(0, 'end')
                self.console_entry.insert(0, next)

    def choose_spec_save_dir(self):

        self.remote_file_explorer = RemoteFileExplorer(self,
                                                       label='Select a directory to save raw spectral data.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\\RiceData\\MarsGroup\\YourName\\spectral_data',
                                                       target=self.spec_save_dir_entry)

    def choose_process_input_dir(self):
        r = RemoteFileExplorer(self,
                               label='Select the directory containing the data you want to process.\nThis must be on a drive mounted on the spectrometer control computer.\n E.g. R:\\RiceData\\MarsGroup\\YourName\\spectral_data',
                               target=self.input_dir_entry)

    def choose_process_output_dir(self):
        r = RemoteFileExplorer(self,
                               label='Select the directory where you want to save your processed data.\nThis must be to a drive mounted on the spectrometer control computer.\n E.g. R:\\RiceData\\MarsGroup\\YourName\\spectral_data',
                               target=self.output_dir_entry)

    def add_sample(self):
        try:
            self.add_sample_button.pack_forget()
        except:
            self.add_sample_button = Button(self.samples_frame, text='Add new', command=self.add_sample, width=10,
                                            fg=self.buttontextcolor, bg=self.buttonbackgroundcolor, bd=self.bd)
            self.tk_buttons.append(self.add_sample_button)
            self.add_sample_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                          bg=self.buttonbackgroundcolor, state=DISABLED)

        self.sample_frames.append(Frame(self.samples_frame, bg=self.bg))
        self.sample_frames[-1].pack(pady=(5, 0))

        self.control_frame.min_height += 50
        self.control_frame.update()

        self.sample_pos_vars.append(StringVar(self.master))
        self.sample_pos_vars[-1].trace('w', self.set_taken_sample_positions)
        menu_positions = []
        pos_set = False
        for pos in self.available_sample_positions:
            if pos in self.taken_sample_positions:
                pass
            elif pos_set == False:
                self.sample_pos_vars[-1].set(pos)
                pos_set = True
            else:
                menu_positions.append(pos)
        if len(
                menu_positions) == 0:  # If all samples are full (i.e. this is the last sample), we need to have a value in the menu options in order for it to appear on the screen. This is really a duplicate option, but Tkinter won't create an OptionMenu without options.
            menu_positions.append(self.sample_pos_vars[-1].get())

        self.pos_menus.append(OptionMenu(self.sample_frames[-1], self.sample_pos_vars[-1], *menu_positions))
        self.pos_menus[-1].configure(width=8, highlightbackground=self.highlightbackgroundcolor)
        self.pos_menus[-1].pack(side=LEFT)
        self.option_menus.append(self.pos_menus[-1])

        self.sample_labels.append(
            Label(self.sample_frames[-1], bg=self.bg, fg=self.textcolor, text='Label:', padx=self.padx, pady=self.pady))
        self.sample_labels[-1].pack(side=LEFT, padx=(5, 0))

        self.sample_label_entries.append(Entry(self.sample_frames[-1], width=20, bd=self.bd, bg=self.entry_background,
                                               selectbackground=self.selectbackground,
                                               selectforeground=self.selectforeground))

        self.entries.append(self.sample_label_entries[-1])
        self.sample_label_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.sample_removal_buttons.append(Button(self.sample_frames[-1], text='Remove',
                                                  command=lambda x=len(self.sample_removal_buttons): self.remove_sample(
                                                      x), width=7, fg=self.buttontextcolor,
                                                  bg=self.buttonbackgroundcolor, bd=self.bd))
        self.sample_removal_buttons[-1].config(fg=self.buttontextcolor,
                                               highlightbackground=self.highlightbackgroundcolor,
                                               bg=self.buttonbackgroundcolor)
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

    def set_taken_sample_positions(self, arg1=None, arg2=None, arg3=None):
        self.taken_sample_positions = []
        for var in self.sample_pos_vars:
            self.taken_sample_positions.append(var.get())

        # Now remake all option menus with taken sample positions not listed in options unless that was the option that was already selected for them.
        menu_positions = []
        for pos in self.available_sample_positions:
            if pos in self.taken_sample_positions:
                pass
            else:
                menu_positions.append(pos)

        for i, menu in enumerate(self.pos_menus):
            local_menu_positions = list(menu_positions)
            if len(
                    menu_positions) == 0:  # If all samples are full, we need to have a value in the menu options in order for it to appear on the screen. This is really a duplicate option, but Tkinter won't create an OptionMenu without options, so having it in there prevents errors.
                local_menu_positions.append(self.sample_pos_vars[i].get())
            self.pos_menus[i]['menu'].delete(0, 'end')
            for choice in local_menu_positions:
                self.pos_menus[i]['menu'].add_command(label=choice, command=tk._setit(self.sample_pos_vars[i], choice))

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
        except:
            self.add_geometry_button = Button(self.individual_angles_frame, text='Add new', command=self.add_geometry,
                                              width=10, fg=self.buttontextcolor, bg=self.buttonbackgroundcolor,
                                              bd=self.bd)
            self.tk_buttons.append(self.add_geometry_button)
            self.add_geometry_button.config(fg=self.buttontextcolor, highlightbackground=self.highlightbackgroundcolor,
                                            bg=self.buttonbackgroundcolor, state=DISABLED)

        self.geometry_frames.append(Frame(self.individual_angles_frame, bg=self.bg))
        self.geometry_frames[-1].pack(pady=(5, 0))

        self.incidence_labels.append(
            Label(self.geometry_frames[-1], bg=self.bg, fg=self.textcolor, text='i:', padx=self.padx, pady=self.pady))
        self.incidence_labels[-1].pack(side=LEFT, padx=(5, 0))
        self.incidence_entries.append(Entry(self.geometry_frames[-1], width=10, bd=self.bd, bg=self.entry_background,
                                            selectbackground=self.selectbackground,
                                            selectforeground=self.selectforeground))
        self.entries.append(self.incidence_entries[-1])
        self.incidence_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.emission_labels.append(
            Label(self.geometry_frames[-1], padx=self.padx, pady=self.pady, bg=self.bg, fg=self.textcolor, text='e:'))
        self.emission_labels[-1].pack(side=LEFT)
        self.emission_entries.append(Entry(self.geometry_frames[-1], width=10, bd=self.bd, bg=self.entry_background,
                                           selectbackground=self.selectbackground,
                                           selectforeground=self.selectforeground))
        self.entries.append(self.emission_entries[-1])
        self.emission_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.azimuth_labels.append(
            Label(self.geometry_frames[-1], bg=self.bg, fg=self.textcolor, text='az:', padx=self.padx, pady=self.pady))
        self.azimuth_labels[-1].pack(side=LEFT, padx=(5, 0))
        self.azimuth_entries.append(Entry(self.geometry_frames[-1], width=10, bd=self.bd, bg=self.entry_background,
                                          selectbackground=self.selectbackground,
                                          selectforeground=self.selectforeground))
        self.entries.append(self.azimuth_entries[-1])
        self.azimuth_entries[-1].pack(side=LEFT, padx=(0, 10))

        self.geometry_removal_buttons.append(Button(self.geometry_frames[-1], text='Remove', command=lambda
            x=len(self.geometry_removal_buttons): self.remove_geometry(x), width=7, fg=self.buttontextcolor,
                                                    bg=self.buttonbackgroundcolor, bd=self.bd))
        self.geometry_removal_buttons[-1].config(fg=self.buttontextcolor,
                                                 highlightbackground=self.highlightbackgroundcolor,
                                                 bg=self.buttonbackgroundcolor)
        if len(self.incidence_entries) > 1:
            for button in self.geometry_removal_buttons:
                button.pack(side=LEFT)

        if len(self.incidence_entries) > 10:
            self.add_geometry_button.configure(state=DISABLED)
        self.add_geometry_button.pack(pady=(15, 10))

    def configure_pi(self, i=None, e=None, az=None, pos=None):
        if i == None: i = self.motor_i
        if e == None: e = self.motor_e
        if pos == None: pos = self.sample_tray_index

        self.pi_commander.configure(str(i), str(e), pos)

        timeout_s = PI_BUFFER
        while timeout_s > 0:
            if 'piconfigsuccess' in self.pi_listener.queue:
                self.pi_listener.queue.remove('piconfigsuccess')
                if pos != -1:
                    tray_position_string = self.available_sample_positions[int(pos) - 1]
                else:
                    tray_position_string = 'WR'
                self.goniometer_view.set_current_sample(tray_position_string)

                if i != None:
                    self.motor_i = i
                if e != None:
                    self.motor_e = e
                if az != None:
                    self.motor_az = AZIMUTH_HOME

                self.log('Raspberry pi configured.\n\ti = ' + str(self.motor_i) + '\n\te = ' + str(
                    self.motor_e) + '\n\taz = ' + str(self.motor_az) + '\n\ttray position: ' + tray_position_string)
                break

            time.sleep(INTERVAL)
            timeout_s -= INTERVAL

        if timeout_s <= 0:
            self.queue = []
            self.script_running = False
            if self.wait_dialog == None:
                dialog = ErrorDialog(self,
                                     label='Error: Failed to configure Raspberry Pi.\nCheck connections and/or restart scripts.')

            else:  # Everything in this else clause is nonsense.
                self.wait_dialog.interrupt(
                    'Error: Failed to configure Raspberry Pi.\nCheck connections and/or restart scripts.')

            self.motor_i = None
            self.motor_e = None
            self.motor_az = None
            self.set_manual_automatic(force=0)

            return
        else:
            self.goniometer_view.set_azimuth(self.motor_az, config=True)
            self.goniometer_view.set_incidence(self.motor_i, config=True)
            self.goniometer_view.set_emission(self.motor_e, config=True)
            self.complete_queue_item()

            if len(self.queue) > 0:
                self.next_in_queue()
            else:
                self.unfreeze()

    def set_manual_automatic(self, override=False, force=-1, known_goniometer_state=False):
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

            self.opt_button.pack(padx=self.padx, pady=self.pady, side=LEFT)
            self.wr_button.pack(padx=self.padx, pady=self.pady, side=LEFT)
            self.spec_button.pack(padx=self.padx, pady=self.pady, side=LEFT)

            self.acquire_button.pack_forget()
            menu.entryconfigure(0, label='X Manual')
            menu.entryconfigure(1, label='  Automatic')
            self.geommenu.entryconfigure(0, label='X Individual')
            self.geommenu.entryconfigure(1, state=DISABLED, label='  Range (Automatic only)')
        else:

            self.add_geometry_button.configure(state=NORMAL)
            self.acquire_button.pack(padx=self.padx, pady=self.pady)
            self.spec_button.pack_forget()
            self.opt_button.pack_forget()
            self.wr_button.pack_forget()
            self.range_radio.configure(state=NORMAL)
            self.add_sample_button.configure(state=NORMAL)
            for pos_menu in self.pos_menus:
                pos_menu.configure(state=NORMAL)

            self.queue.insert(0, {self.configure_pi: []})
            # This is if you are setting manual_automatic from commandline and already entered i, e, sample tray position.
            if known_goniometer_state:
                menu.entryconfigure(0, label='  Manual')
                menu.entryconfigure(1, label='X Automatic')
                self.geommenu.entryconfigure(1, state=NORMAL, label='  Range (Automatic only)')
            else:
                self.freeze()
                buttons = {
                    'ok': {
                        self.next_in_queue: [],
                        self.unfreeze: [],
                    },
                    'cancel': {
                        self.unfreeze: [],
                        self.set_manual_automatic: [override, 0],
                        self.clear_queue: [],

                    }
                }
                dialog = IntInputDialog(self, title='Setup Required',
                                        label='Setup required: Unknown goniometer state.\n\nPlease enter the current incidence, emission, and tray positions and click OK. \nNote that this will trigger the azimuth table homing routine.\n\nAlternatively, click \'Cancel\' to use the goniometer in manual mode.',
                                        values={'Incidence': [self.motor_i, self.min_motor_i, self.max_motor_i],
                                                'Emission': [self.motor_e, self.min_motor_e, self.max_motor_e],
                                                'Tray position': [self.sample_tray_index, 0, self.num_samples - 1]},
                                        buttons=buttons)

            menu.entryconfigure(0, label='  Manual')
            menu.entryconfigure(1, label='X Automatic')
            self.geommenu.entryconfigure(1, state=NORMAL, label='  Range (Automatic only)')

    def clear_queue(self):
        self.queue = []

    def set_individual_range(self, force=-1):
        # TODO: save individually specified angles to config file
        if force == 0:
            self.range_frame.pack_forget()
            self.individual_angles_frame.pack()
            self.geommenu.entryconfigure(0, label='X Individual')
            self.geommenu.entryconfigure(1, label='  Range (Automatic only)')
            self.individual_range.set(0)
        elif force == 1:
            self.individual_angles_frame.pack_forget()
            self.range_frame.pack()
            self.geommenu.entryconfigure(0, label='  Individual')
            self.geommenu.entryconfigure(1, label='X Range (Automatic only)')
            self.individual_range.set(1)

    def set_overwrite_all(self, val):
        self.overwrite_all = val

    def validate_input_dir(self, *args):
        pos = self.input_dir_entry.index(INSERT)
        input_dir = rm_reserved_chars(self.input_dir_entry.get())
        if len(input_dir) < len(self.input_dir_entry.get()):
            pos = pos - 1
        self.input_dir_entry.delete(0, 'end')
        self.input_dir_entry.insert(0, input_dir)
        self.input_dir_entry.icursor(pos)

    def validate_output_dir(self):
        pos = self.output_dir_entry.index(INSERT)
        output_dir = rm_reserved_chars(self.output_dir_entry.get())
        if len(output_dir) < len(self.output_dir_entry.get()):
            pos = pos - 1
        self.output_dir_entry.delete(0, 'end')
        self.output_dir_entry.insert(0, output_dir)
        self.output_dir_entry.icursor(pos)

    def validate_output_filename(self, *args):
        pos = self.output_filename_entry.index(INSERT)
        filename = rm_reserved_chars(self.spec_output_filename_entry.get())
        filename = filename.strip('/').strip('\\')
        self.output_filename_entry.delete(0, 'end')
        self.output_filename_entry.insert(0, filename)
        self.output_filename_entry.icursor(pos)

    def validate_spec_save_dir(self, *args):
        pos = self.spec_save_dir_entry.index(INSERT)
        spec_save_dir = rm_reserved_chars(self.spec_save_dir_entry.get())
        if len(spec_save_dir) < len(self.spec_save_dir_entry.get()):
            pos = pos - 1
        self.spec_save_dir_entry.delete(0, 'end')
        self.spec_save_dir_entry.insert(0, spec_save_dir)
        self.spec_save_dir_entry.icursor(pos)

    def validate_basename(self, *args):
        pos = self.spec_basename_entry.index(INSERT)
        basename = rm_reserved_chars(self.spec_basename_entry.get())
        basename = basename.strip('/').strip('\\')
        self.spec_basename_entry.delete(0, 'end')
        self.spec_basename_entry.insert(0, basename)
        self.spec_basename_entry.icursor(pos)

    def validate_startnum(self, *args):
        pos = self.spec_startnum_entry.index(INSERT)
        num = numbers_only(self.spec_startnum_entry.get())
        if len(num) > NUMLEN:
            num = num[0:NUMLEN]
        if len(num) < len(self.spec_startnum_entry.get()):
            pos = pos - 1
        self.spec_startnum_entry.delete(0, 'end')
        self.spec_startnum_entry.insert(0, num)
        self.spec_startnum_entry.icursor(pos)

    def validate_sample_name(self, name):
        # print(entry)
        # pos=entry.index(INSERT)
        # name=entry.get()
        name = name.replace('(', '').replace(')', '').replace('i=', 'i').replace('e=', 'e').replace(':', '')
        return name
        # entry.delete(0,'end')
        # entry.insert(0,name)
        # entry.icursor(pos)

    # motor_az input from -90 to 270
    # science az from 0 to 179.
    # az=180, i=50 is the same position as az=0, i=-50
    def motor_pos_to_science_pos(self, motor_i, motor_e, motor_az):
        if motor_az < self.min_motor_az:
            print('UNEXPECTED AZ: ' + str(motor_az))
        if motor_az > self.max_motor_az:
            print('UNEXPECTED AZ: ' + str(motor_az))
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
    # References: https://www.movable-type.co.uk/scripts/latlong.html
    #            https://en.wikipedia.org/wiki/Great-circle_navigation
    #            http://astrophysicsformulas.com/astronomy-formulas-astrophysics-formulas/angular-distance-between-two-points-on-a-sphere
    def get_closest_approach(self, i, e, az, print_me=False):

        def cos(theta):
            return np.cos(theta * 3.14159 / 180)

        def sin(theta):
            return np.sin(theta * 3.14159 / 180)

        def arccos(ratio):
            return np.arccos(ratio) * 180 / 3.14159

        def arctan2(y, x):
            return np.arctan2(y, x) * 180 / 3.14159

        def arctan(ratio):
            return np.arctan(ratio) * 180 / 3.14159

        #         need to subtract component that is in same direction
        #         or add component in opposite direction
        #         for az=0: full component in same or opposite
        #         az=90: no component in same or opposite
        #         component in same plane is cos(az) or, if az > 90, cos(180-az)
        def get_lat1_lat2_delta_long(i, e, az):
            if np.sign(i) == np.sign(e):
                delta_long = az
            else:
                delta_long = 180 - az
            lat1 = 90 - np.abs(i)
            lat2 = 90 - np.abs(e)
            return lat1, lat2, delta_long

        def get_angular_distance(i, e, az):
            lat1, lat2, delta_long = get_lat1_lat2_delta_long(i, e, az)
            dist = np.abs(arccos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(delta_long)))
            return dist

        def get_initial_bearing(e):
            lat2 = 90 - np.abs(e)
            bearing = arctan2(cos(lat2), sin(lat2))
            return bearing

        i, e, az = self.motor_pos_to_science_pos(i, e, az)
        closest_dist = get_angular_distance(i, e, az)
        closest_pos = (i, e, az)

        return closest_pos, closest_dist

        # check if the fiber optic cable will hit the light source arm
        # start by defining a list of positions of the light source arm
        if False:  # Fiber optic tucked under incidence arm, no collision possible.
            arm_positions = []
            arm_bottom_i = 90
            arm_bottom_az = az - 90

            arm_top_i = np.abs(i)
            if np.sign(i) != np.sign(e):
                arm_top_az = arm_bottom_az - 90
            else:
                arm_top_az = arm_bottom_az + 90
            #             print('arm top az:')

            bearing = get_initial_bearing(arm_top_i)

            if print_me:
                print('bearing: ' + str(bearing))
            points = np.arange(0, 90, 3)
            points = np.append(points, 90)
            arm_lat = []
            arm_delta_long = []
            if print_me:
                print(points)
            for point in points:
                tan_lat = cos(bearing) * sin(point) / np.sqrt(cos(point) ** 2 + sin(bearing) ** 2 * sin(point) ** 2)
                lat = arctan(tan_lat)
                arm_lat.append(lat)
                tan_long = sin(bearing) * sin(point) / cos(point)
                long = arctan(tan_long)

                arm_delta_long.append(long)

            arm_delta_long = np.array(arm_delta_long)
            if np.sign(i) != np.sign(e):
                arm_azes = arm_bottom_az - arm_delta_long

            #                 arm_top_az=arm_bottom_az-90
            else:
                #                 arm_top_az=arm_bottom_az+90
                arm_azes = arm_bottom_az + arm_delta_long

            if False:
                print('arm bottom az')
                print(arm_bottom_az)
                print('arm lat:')
                print(arm_lat)
                print('arm long: ')
                print(arm_azes)

            for num, lat in enumerate(arm_lat):
                arm_i = 90 - lat
                fiber_collision_e = np.abs(e)
                pos = [arm_i, fiber_collision_e, arm_azes[num]]
                if False:
                    print('*****')
                    print(fiber_collision_e)
                    print(arm_i)
                    print(arm_azes[num])

                dist = get_angular_distance(arm_i, fiber_collision_e, arm_azes[num])
                #                 print('Distance: '+str(dist))
                if dist < closest_dist:
                    closest_dist = dist
                    closest_pos = pos
                if dist < self.required_angular_separation:
                    if False:
                        print('FIBER OPTIC COLLISION')

        if i <= 0:  # Can run into detector arm
            # define a list of positions of the detector arm
            arm_positions = []
            arm_bottom_e = 90
            arm_bottom_az = az - 90  # -90 to 90 because i is negative.

            if e <= 0:  # azimuth is azimuth
                arm_top_e = -1 * e
                arm_top_az = arm_bottom_az + 90  # *sin(-e)
            else:
                arm_top_e = e
                arm_top_az = arm_bottom_az - 90  # *sin(e)

            bearing = get_initial_bearing(arm_top_e)
            if print_me:
                print('bearing: ' + str(bearing))
            points = np.arange(0, 90, 3)
            points = np.append(points, 90)
            arm_lat = []
            arm_delta_long = []
            if print_me:
                print(points)
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
            if print_me:
                print('arm lat:')
                print(arm_lat)
                print('arm long: ')
                print(arm_delta_long)

            for num, lat in enumerate(arm_lat):
                arm_e = 90 - lat
                pos = [i, -1 * arm_e, arm_bottom_az + arm_delta_long[num]]
                if print_me:
                    print(i)
                    print(arm_e)
                dist = get_angular_distance(i, -1 * arm_e, arm_azes[num])
                if dist < closest_dist:
                    closest_dist = dist
                    closest_pos = pos

        return closest_pos, closest_dist

    def validate_distance(self, i, e, az, print_me=False):
        try:
            i = int(i)
            e = int(e)
            az = int(az)
        except:
            return False

        closest_pos, closest_dist = self.get_closest_approach(i, e, az, print_me=False)
        if closest_dist < self.required_angular_separation:
            if print_me:
                print('COLLISION')
                print(i)
                print(e)
                print(az)
            return False
        else:
            return True

    def clear(self):
        if self.manual_automatic.get() == 0:
            self.unfreeze()
            self.active_incidence_entries[0].delete(0, 'end')
            self.active_emission_entries[0].delete(0, 'end')
            self.active_azimuth_entries[0].delete(0, 'end')
            self.sample_label_entries[self.current_sample_gui_index].delete(0, 'end')

    def next_in_queue(self):
        #         for line in traceback.format_stack():
        #             print(line.strip())
        dict = self.queue[0]
        for func in dict:
            args = dict[func]
            func(*args)

    def refresh(self):
        time.sleep(0.25)
        self.goniometer_view.flip()
        self.master.update()

    def resize(self,
               window=None):  # Resize the console and goniometer view frames to be proportional sizes, and redraw the goniometer.
        if window == None:
            window = PretendEvent(self.master, self.master.winfo_width(), self.master.winfo_height())
        if window.widget == self.master:
            reserve_width = 500
            try:
                width = self.console_frame.winfo_width()
                # g_height=self.goniometer_view.double_embed.winfo_height()

                console_height = int(window.height / 3) + 10
                if console_height < 200: console_height = 200
                goniometer_height = window.height - console_height + 10
                self.goniometer_view.double_embed.configure(height=goniometer_height)
                self.console_frame.configure(height=console_height)
                self.view_notebook.configure(height=goniometer_height)
                self.plotter.set_height(goniometer_height)

                thread = Thread(
                    target=self.refresh)  # I don't understand why this is needed, but things don't seem to get drawn right without it.
                thread.start()

                self.goniometer_view.draw_side_view(window.width - self.control_frame.winfo_width() - 2,
                                                    goniometer_height - 10)
                self.goniometer_view.flip()
                self.master.update()
            except AttributeError:
                # Happens when the program is just starting up and there is no view yet
                pass
            except ValueError:
                pass

    def finish_move(self):
        self.goniometer_view.draw_circle()

    def complete_queue_item(self):
        self.queue.pop(0)

    def rm_current(self):
        self.spec_commander.delete_spec(self.spec_save_dir_entry.get(), self.spec_basename_entry.get(),
                                        self.spec_startnum_entry.get())

        t = BUFFER
        while t > 0:
            if 'rmsuccess' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmsuccess')

                return True
            elif 'rmfailure' in self.spec_listener.queue:
                self.spec_listener.queue.remove('rmfailure')
                return False
            t = t - INTERVAL
            time.sleep(INTERVAL)
        return False

    def choose_process_output_dir(self):
        init_dir = self.output_dir_entry.get()
        if self.proc_remote.get():
            process_file_explorer = RemoteFileExplorer(self, target=self.output_dir_entry, title='Select a directory',
                                                       label='Select an output directory for processed data.',
                                                       directories_only=True)
        else:
            self.process_top.lift()
            if os.path.isdir(init_dir):
                dir = askdirectory(initialdir=init_dir, title='Select an output directory')
            else:
                dir = askdirectory(initialdir=os.getcwd(), title='Select an output directory')
            if dir != ():
                self.output_dir_entry.delete(0, 'end')
                self.output_dir_entry.insert(0, dir)
        self.process_top.lift()

    def choose_plot_file(self):
        init_file = self.plot_input_dir_entry.get()
        relative_file = init_file.split('/')[-1].split('\\')[-1]
        init_dir = init_file.strip(relative_file)
        if self.plot_remote.get():
            plot_file_explorer = RemoteFileExplorer(self, target=self.plot_input_dir_entry, title='Select a file',
                                                    label='Select a file to plot', directories_only=False)
        else:
            if os.path.isdir(init_dir):
                file = askopenfilename(initialdir=init_dir, title='Select a file to plot')
            else:
                file = askopenfilename(initialdir=os.getcwd(), title='Select a file to plot')
            if file != ():
                self.plot_input_dir_entry.delete(0, 'end')
                self.plot_input_dir_entry.insert(0, file)
        self.plot_top.lift()

    def log(self, info_string, write_to_file=False):
        write_to_file = False  # Used to write to a local log file, but now we only write to a log file in the raw spectral data directory.
        # self.check_logfile()
        self.master.update()
        space = self.console_log.winfo_width()
        space = str(int(space / 8.5))
        if int(space) < 20:
            space = str(20)
        datestring = ''
        datestringlist = str(datetime.datetime.now()).split('.')[:-1]
        for d in datestringlist:
            datestring = datestring + d

        while info_string[0] == '\n':
            info_string = info_string[1:]

        if write_to_file:
            info_string_copy = str(info_string)

        if '\n' in info_string:
            lines = info_string.split('\n')

            lines[0] = ('{1:' + space + '}{0}').format(datestring, lines[0])
            for i in range(len(lines)):
                if i == 0:
                    continue
                else:
                    lines[i] = ('{1:' + space + '}{0}').format('', lines[i])
            info_string = '\n'.join(lines)
        else:
            info_string = ('{1:' + space + '}{0}').format(datestring, info_string)

        if info_string[-2:-1] != '\n':
            info_string += '\n'

        self.console_log.insert(END, info_string + '\n')
        self.console_log.see(END)

    def freeze(self):
        for button in self.tk_buttons:
            try:
                button.configure(state='disabled')
            except:
                pass
        for entry in self.entries:
            try:
                entry.configure(state='disabled')
            except:
                pass
        for radio in self.radiobuttons:
            try:
                radio.configure(state='disabled')
            except:
                pass

        for button in self.tk_check_buttons:
            try:
                button.configure(state='disabled')
            except:
                pass

        for menu in self.option_menus:
            try:
                menu.configure(state='disabled')
            except:
                pass

        self.menubar.entryconfig('Settings', state='disabled')
        self.filemenu.entryconfig(0, state=DISABLED)
        self.filemenu.entryconfig(1, state=DISABLED)

        self.console_entry.configure(state='disabled')

    def unfreeze(self):
        self.console_entry.configure(state='normal')
        self.menubar.entryconfig('Settings', state='normal')
        self.filemenu.entryconfig(0, state=NORMAL)
        self.filemenu.entryconfig(1, state=NORMAL)
        for button in self.tk_buttons:
            try:
                button.configure(state='normal')
            except Exception as e:
                print(e)
        for entry in self.entries:
            try:
                entry.configure(state='normal')
            except Exception as e:
                print(e)
        for radio in self.radiobuttons:
            try:
                radio.configure(state='normal')
            except Exception as e:
                print(e)

        for button in self.tk_check_buttons:
            try:
                button.configure(state='normal')
            except:
                pass

        for menu in self.option_menus:
            try:
                menu.configure(state='normal')
            except:
                pass

        if self.manual_automatic.get() == 0:
            self.range_radio.configure(state='disabled')
            self.add_geometry_button.configure(state='disabled')
            self.add_sample_button.configure(state='disabled')
            for pos_menu in self.pos_menus:
                pos_menu.configure(state='disabled')

    def light_close(self):
        self.pi_commander.move_light(self.active_incidence_entries[0].get())
        handler = CloseHandler(self)
        self.goniometer_view.set_incidence(int(self.active_incidence_entries[0].get()))

    def detector_close(self):
        self.pi_commander.move_detector(self.active_emission_entries[0].get())
        handler = CloseHandler(self)
        self.goniometer_view.set_emission(int(self.active_emission_entries[0].get()))

    def plot_right_click(self, event):
        return
        dist_to_edge = self.dist_to_edge(event)
        if dist_to_edge == None:  # not on a tab
            return

        else:
            index = self.view_notebook.index("@%d,%d" % (event.x, event.y))
            if index != 0:
                self.view_notebook.forget(index)
                self.view_notebook.event_generate("<<NotebookTabClosed>>")