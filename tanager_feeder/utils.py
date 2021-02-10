from enum import Enum
import os
import psutil
from tkinter import Frame, Scrollbar, StringVar, Canvas, VERTICAL, TRUE, FALSE, RIGHT, Y, NW, LEFT, BOTH, Listbox
from typing import Any

AZIMUTH_HOME = 0
INTERVAL = 0.25
BUFFER = 15
PI_BUFFER = 20


class ConnectionTracker:
    PI_PORT = 12345
    SPEC_PORT = 54321
    CONTROL_PORT = 12345

    def __init__(self, spec_ip="192.168.86.50", pi_ip="raspberrypi"):
        self.spec_offline = False
        self.pi_offline = False
        self.spec_ip = spec_ip
        self.pi_ip = pi_ip


class ConfigInfo:
    def __init__(self, local_config_loc, global_config_loc, icon_loc, num_len, opsys):
        self.local_config_loc = local_config_loc
        self.global_config_loc = global_config_loc
        self.icon_loc = icon_loc
        self.opsys = opsys
        self.num_len = num_len


# Which spectrometer computer are you using? This should probably be desktop, but could be 'new' for the new lappy or
# 'old' for the ancient laptop.
computer = "desktop"
computer = "new"


def limit_len(input, max):
    return input[:max]


def validate_int_input(input, min, max):
    try:
        input = int(input)
    except:
        return False
    if input > max:
        return False
    if input < min:
        return False
    return True


def validate_float_input(input: Any, min: float, max: float):
    try:
        input = float(input)
    except:
        return False
    if input > max:
        return False
    if input < min:
        return False
    return True


def decrypt(encrypted):
    cmd = encrypted.split("&")[0]
    params = encrypted.split("&")[1:]
    i = 0
    for param in params:
        params[i] = param.replace("+", "\\").replace("=", ":")
        params[i] = params[i].replace("++", "+")
        i = i + 1
    return cmd, params


def rm_reserved_chars(input):
    output = (
        input.replace("&", "")
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


def numbers_only(input):
    output = ""
    for digit in input:
        if (
            digit == "1"
            or digit == "2"
            or digit == "3"
            or digit == "4"
            or digit == "5"
            or digit == "6"
            or digit == "7"
            or digit == "8"
            or digit == "9"
            or digit == "0"
        ):
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
    def __init__(self, controller):
        self.position = "Sample 1"


# http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame


class VerticalScrolledFrame(Frame):

    # Use the 'interior' attribute to place widgets inside the scrollable frame
    # Construct and pack/place/grid normally
    # This frame only allows vertical scrolling

    def __init__(self, controller, parent, min_height=600, width=468, *args, **kw):
        self.controller = controller
        Frame.__init__(self, parent, *args, **kw)

        self.min_height = min_height  # Miniumum height for interior frame to show all elements. Changes as new samples or viewing geometries are added.

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
        )  # This makes it so we can easily manually set the interior frame's size as needed. See _configure_canvas() for how it's done.
        self.interior_id = canvas.create_window(0, 0, window=interior, anchor=NW)
        self.canvas.bind("<Configure>", self._configure_canvas)
        self.width = width

    def _configure_canvas(self, event):
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
    def __init__(self, frame, bg, entry_background, listboxhighlightcolor, selectmode=tkinter.SINGLE):

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

    def destroy(self):
        self.scrollbar.destroy()
        super().destroy()


def exit_func():
    print("Exiting TANAGER Feeder.")
    current_system_pid = os.getpid()
    tanager_feeder_process = psutil.Process(current_system_pid)
    tanager_feeder_process.terminate()


class MovementUnits(Enum):
    ANGLE = "angle"
    STEPS = "steps"
    POSITION = "position"