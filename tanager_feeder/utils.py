from enum import Enum
import os
from threading import Thread
from tkinter import (
    Frame,
    Scrollbar,
    StringVar,
    Canvas,
    Event,
    VERTICAL,
    TRUE,
    FALSE,
    RIGHT,
    Y,
    NW,
    LEFT,
    BOTH,
    Listbox,
    SINGLE,
    Widget,
    END,
)
from typing import Any, Optional, Union
import time

import numpy as np
import psutil

from tanager_tcp import TanagerClient

AZIMUTH_HOME = 0
INTERVAL = 0.25
BUFFER = 15
PI_BUFFER = 20


# These are related to the region of spectra that are sensitive to polarization artifacts. This is at high phase
# angles between 1000 and 1400 nm.
MIN_WAVELENGTH_ARTIFACT_FREE = 1000
MAX_WAVELENGTH_ARTIFACT_FREE = 1400
MIN_G_ARTIFACT_FREE = -20
MAX_G_ARTIFACT_FREE = 40

computer = "new"
NUMLEN = None  # number of digits in the raw data filename. Could change from one version of software to next.
if computer == "old":
    # Number of digits in spectrum number for spec save config
    NUMLEN = 3
elif computer == "desktop":
    # Number of digits in spectrum number for spec save config
    NUMLEN = 5
    # Time added to timeouts to account for time to read/write files
elif computer == "new":
    # Number of digits in spectrum number for spec save config
    NUMLEN = 5


class ConnectionManager:
    LISTEN_FOR_PI_PORT = 12345
    LISTEN_FOR_SPEC_PORT = 54321
    REMOTE_PORT = 12345

    def __init__(self, spec_ip="192.168.86.50", pi_ip="raspberrypi"):
        self.spec_offline = True
        self.pi_offline = True
        self._spec_ip = spec_ip
        self._pi_ip = pi_ip
        self.spec_client = TanagerClient((spec_ip, self.REMOTE_PORT), self.LISTEN_FOR_SPEC_PORT)
        self.pi_client = TanagerClient((pi_ip, self.REMOTE_PORT), self.LISTEN_FOR_PI_PORT)

    @property
    def spec_ip(self):
        return self._spec_ip

    @spec_ip.setter
    def spec_ip(self, new_ip):
        self._spec_ip = new_ip
        self.spec_client = TanagerClient((new_ip, self.REMOTE_PORT), self.LISTEN_FOR_SPEC_PORT)

    @property
    def pi_ip(self):
        return self._pi_ip

    @pi_ip.setter
    def pi_ip(self, new_ip):
        self._pi_ip = new_ip
        self.pi_client = TanagerClient((new_ip, self.REMOTE_PORT), self.LISTEN_FOR_PI_PORT)

    def send_to_spec(self, message: str) -> bool:
        if not self.spec_offline:
            sent = self.spec_client.send(message)
            if not sent:
                self.spec_offline = True
            return sent
        return False

    def send_to_pi(self, message: str) -> bool:
        if not self.pi_offline:
            sent = self.pi_client.send(message)
            if not sent:
                self.pi_offline = True
            return sent
        return False

    def connect_spec(self, timeout: float):
        self.spec_offline = not self.spec_client.connect(timeout)
        return not self.spec_offline

    def connect_pi(self, timeout: float):
        self.pi_offline = not self.pi_client.connect(timeout)
        return not self.pi_offline


class ConfigInfo:
    def __init__(self, local_config_loc, global_config_loc, icon_loc, num_len, opsys):
        self.local_config_loc = local_config_loc
        self.global_config_loc = global_config_loc
        self.icon_loc = icon_loc
        self.opsys = opsys
        self.num_len = num_len

class ControllerType:
    """This class, which is extended by Controller, is defined so as to avoid
      circular imports when adding type hints to classes that are imported by
      Controller and also reference an instance of Controller"""
    def __init__(self, connection_tracker, config_info):
        self.connection_tracker = connection_tracker
        self.config_info = config_info
        self.tk_format = None
        self.view_notebook = None
        self.master = None
        self.incidence_entries = None
        self.azimuth_entries = None
        self.emission_entries = None
        self.opt = None
        self.wr = None
        self.min_science_i = None
        self.max_science_i = None
        self.min_science_e = None
        self.max_science_e = None
        self.min_science_az = None
        self.max_science_az = None
        self.check_viewing_geom_for_manual_operation = None
        self.spec_config_count = None
        self.sample_label_entries = None
        self.current_sample_gui_index = None
        self.validate_sample_name = None
        self.log = None
        self.instrument_config_entry = None
        self.manual_automatic = None

        # for plot_manager
        self.plot = None
        self.plotter = None
        self.goniometer_view = None

        # for process_manager
        self.remote_directory_worker = None
        self.process_cmd = None
        self.plot_manager = None
        self.script_running = None
        self.spec_listener = None
        self.spec_commander = None
        self.text_only = None
        self.next_in_queue = None

        # for console
        self.execute_cmd = None
        self.control_frame= None
        self.view_frame = None

        # for cli_manager
        self.set_manual_automatic = None
        self.fail_script_command = None
        self.min_motor_i = None
        self.max_motor_i = None
        self.min_motor_e = None
        self.max_motor_e = None
        self.min_motor_az = None
        self.max_motor_az = None

        self.configure_pi = None
        self.take_spectrum = None
        self.acquire = None
        self.add_geometry = None
        self.set_individual_range = None
        self.individual_range = None
        self.light_start_entry = None
        self.light_end_entry = None
        self.detector_start_entry = None
        self.detector_end_entry = None
        self.azimuth_start_entry = None
        self.azimuth_end_entry = None
        self.light_increment_entry = None
        self.detector_increment_entry = None
        self.azimuth_increment_entry = None

        self.incidence_entries = None
        self.emission_entries = None
        self.azimuth_entries = None

        self.sample_frames = None
        self.available_sample_positions = None
        self.taken_sample_positions = None
        self.remove_sample = None
        self.add_sample = None
        self.set_taken_sample_positions = None
        self.unfreeze = None
        self.spec_save_dir_entry = None
        self.sample_pos_vars = None
        self.spec_basename_entry = None
        self.spec_startnum_entry = None
        self.set_save_config = None
        self.configure_instrument = None
        self.wait_dialog = None
        self.move_tray = None
        self.set_emission = None
        self.set_incidence = None
        self.set_azimuth = None
        self.get_movements = None
        self.console = None



# Which spectrometer computer are you using? This should probably be desktop, but could be 'new' for the new lappy or
# 'old' for the ancient laptop.
computer = "desktop"
computer = "new"


def limit_len(input_str, max_len):
    return input_str[:max_len]


def validate_int_input(input_int: Any, min_int: int, max_int: int):
    try:
        input_int = int(input_int)
    except (ValueError, TypeError):
        # TODO: all valueerror exception catching should probably be value, type
        return False
    if input_int > max_int:
        return False
    if input_int < min_int:
        return False
    return True


def validate_float_input(input_float: Any, min_float: float, max_float: float):
    try:
        input_float = float(input_float)
    except ValueError:
        return False
    if input_float > max_float:
        return False
    if input_float < min_float:
        return False
    return True


def decrypt(encrypted):
    cmd = encrypted.split("&")[0]
    params = encrypted.split("&")[1:]
    i = 0
    for param in params:
        params[i] = param
        i = i + 1
    return cmd, params


def rm_reserved_chars(input_str):
    output = (
        input_str.replace("&", "")
        .replace("+", "")
        .replace("=", "")
        .replace("$", "")
        .replace("^", "")
        .replace("*", "")
        .replace("(", "")
        .replace(",", "")
        .replace(")", "")
        .replace("@", "")
        .replace("!", "")
        .replace("#", "")
        .replace("{", "")
        .replace("}", "")
        .replace("[", "")
        .replace("]", "")
        .replace("|", "")
        .replace(",", "")
        .replace("?", "")
        .replace("~", "")
        .replace('"', "")
        .replace("'", "")
        .replace(";", "")
        .replace("`", "")
    )
    return output


def numbers_only(input_str):
    output = ""
    for digit in input_str:
        if digit in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0"):
            output += digit
    return output


class PretendEvent:
    def __init__(self, widget, width, height):
        self.widget = widget
        self.width = width
        self.height = height


class PrivateEntry:
    def __init__(self, text):
        self.text = text

    def get(self):
        return self.text


class SampleFrame:
    def __init__(self):
        self.position = "Sample 1"


class TkFormat:
    def __init__(self, config_info=None):
        # Yay formatting. Might not work for Macs.
        self.bg = "#333333"
        self.textcolor = "light gray"
        self.buttontextcolor = "white"
        self.bd = 2
        self.padx = 3
        self.pady = 3
        self.border_color = "light gray"
        self.button_width = 15
        self.buttonbackgroundcolor = "#888888"
        self.highlightbackgroundcolor = "#222222"
        self.entry_background = "light gray"
        if config_info is None or config_info.opsys == "Windows":
            self.listboxhighlightcolor = "darkgray"
        else:
            self.listboxhighlightcolor = "white"
        self.selectbackground = "#555555"
        self.selectforeground = "white"
        self.check_bg = "#444444"


# http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame
class VerticalScrolledFrame(Frame):

    # Use the 'interior' attribute to place widgets inside the scrollable frame
    # Construct and pack/place/grid normally
    # This frame only allows vertical scrolling

    # pylint: disable = keyword-arg-before-vararg
    def __init__(self, controller, parent, min_height=600, width=468, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        self.controller = controller
        self.min_height = min_height  # Miniumum height for interior frame to show all elements. Changes as new samples
        # or viewing geometries are added.

        # create a canvas object and a vertical scrollbar for scrolling it
        self.scrollbar = Scrollbar(self, orient=VERTICAL)

        self.canvas = canvas = Canvas(self, bd=0, highlightthickness=0, yscrollcommand=self.scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
        canvas.config(width=width)
        # canvas.config(height=height)
        self.scrollbar.config(command=canvas.yview)

        # reset the view
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        # initialize height to the bigger of 1) screen height 2) 700 px

        self.interior = interior = Frame(canvas)
        interior.pack_propagate(
            0
        )  # This makes it so we can easily manually set the interior frame's size as needed. See _configure_canvas()
        # for how it's done.
        self.interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)
        self.canvas.bind("<Configure>", self._configure_canvas)
        self.width = width

    def _configure_canvas(self, event: Optional[Event] = None):
        # pylint: disable = unused-argument
        if self.canvas.winfo_height() > self.min_height:
            self.interior.config(height=self.canvas.winfo_height())
            if self.scrollbar.winfo_ismapped():
                self.scrollbar.pack_forget()
        else:
            self.interior.config(height=self.min_height)
            self.scrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
            # canvas.itemconfigure(interior_id, height=900)
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            if self.canvas.winfo_height() < self.min_height:
                self.canvas.config(width=self.width - 20)
            else:
                self.canvas.config(width=self.width)

            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())

    def update(self, controller_resize=True):
        self._configure_canvas(None)
        if controller_resize:
            self.controller.resize()


class StringVarWithEntry(StringVar):
    def __init__(self):
        super().__init__()
        self.entry = None


class ScrollableListbox(Listbox):
    def __init__(self, frame, bg, entry_background, listboxhighlightcolor, selectmode=SINGLE):

        self.scroll_frame = Frame(frame, bg=bg)
        self.scroll_frame.pack(fill=BOTH, expand=True)
        self.scrollbar = Scrollbar(self.scroll_frame, orient=VERTICAL)
        self.scrollbar.pack(side=RIGHT, fill=Y, padx=(0, 10))
        self.scrollbar.config(command=self.yview)

        super().__init__(
            self.scroll_frame,
            yscrollcommand=self.scrollbar.set,
            selectmode=selectmode,
            bg=entry_background,
            selectbackground=listboxhighlightcolor,
            height=15,
            exportselection=0,
        )
        self.pack(side=LEFT, expand=True, fill=BOTH, padx=(10, 0))
        self.bind('<Control-c>', self.copy)

    def destroy(self):
        self.scrollbar.destroy()
        super().destroy()

    def copy(self, event=None):
        self.clipboard_clear()

        all_items = self.get(0, END)  # tuple with text of all items in Listbox
        sel_idx = self.curselection()  # tuple with indexes of selected items
        sel_list = [all_items[item] for item in sel_idx]  # list with text of all selected items

        for i, text in enumerate(sel_list):
            if i < len(sel_list) -1:
                self.clipboard_append(text+',\n')
            else:
                self.clipboard_append(text)


def exit_func():
    print("Exiting TANAGER Feeder.")
    current_system_pid = os.getpid()
    tanager_feeder_process = psutil.Process(current_system_pid)
    tanager_feeder_process.terminate()


class MovementUnits(Enum):
    ANGLE = "angle"
    STEPS = "steps"
    POSITION = "position"


class CompyTypes(Enum):
    SPEC_COMPY = "spec compy"
    PI = "pi"


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


def get_lat1_lat2_delta_long(i: Union[int, float], e: Union[int, float], az: Union[int, float]):
    if np.sign(i) == np.sign(e):
        delta_long = az
    else:
        delta_long = 180 - az
    lat1 = 90 - np.abs(i)
    lat2 = 90 - np.abs(e)
    return lat1, lat2, delta_long


def get_phase_angle(i: int, e: int, az: int):
    lat1, lat2, delta_long = get_lat1_lat2_delta_long(i, e, az)
    dist = np.abs(arccos(sin(lat1) * sin(lat2) + cos(lat1) * cos(lat2) * cos(delta_long)))
    return dist


def get_initial_bearing(e: int):
    lat2 = 90 - np.abs(e)
    bearing = arctan2(cos(lat2), sin(lat2))
    return bearing


class NotScrolledFrame(Frame):
    def __init__(self, parent, *args, **kw):
        Frame.__init__(self, parent, *args, **kw)
        self.interior = self
        self.scrollbar = NotScrollbar()


class NotScrollbar:
    def __init__(self):
        pass

    def pack_forget(self):
        pass


def set_text(widget: Widget, text: str):
    state = widget.cget("state")
    widget.configure(state="normal")
    widget.delete(0, "end")
    widget.insert(0, text)
    widget.configure(state=state)


def lift_widget(widget: Widget):
    time.sleep(5)
    print("LIFTING WIDGET IN UTILS")
    widget.focus_set()
    widget.lift()


def thread_lift_widget(widget: Widget):
    time.sleep(3)
    print("LIFTING")
    thread = Thread(target=lift_widget, args=(widget,))
    thread.start()
