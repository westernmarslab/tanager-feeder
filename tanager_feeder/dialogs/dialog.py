import tkinter as tk
from tkinter import Frame, Button, Tk, TclError
from typing import Dict, Optional

from tanager_feeder import utils


class Dialog:
    def __init__(
        self,
        controller,
        title: str,
        label: str,
        buttons: Dict,
        width: Optional[int] = None,
        height: Optional[int] = None,
        allow_exit: bool = True,
        button_width: int = 20,
        info_string: Optional[str] = None,
        start_mainloop: bool = True,
    ):
        self.controller = controller

        if self.controller is not None:
            self.tk_format = utils.TkFormat(self.controller.config_info)
            if width is None or height is None:
                self.top = tk.Toplevel(controller.master, bg=self.tk_format.bg)
            else:
                self.top = tk.Toplevel(controller.master, width=width, height=height, bg=self.tk_format.bg)

            if info_string is not None:
                self.controller.log(info_string)
        else:
            self.tk_format = utils.TkFormat()
            self.top = Tk()
            self.top.configure(background=self.tk_format.bg)

        self.top.attributes("-topmost", 1)
        self.top.attributes("-topmost", 0)

        self.label_frame = Frame(self.top, bg=self.tk_format.bg)
        self.label_frame.pack(side=tk.TOP)
        self.__label = tk.Label(self.label_frame, fg=self.tk_format.textcolor, text=label, bg=self.tk_format.bg)
        self.set_label_text(label, log_string=info_string)
        if label != "":
            self.__label.pack(pady=(10, 10), padx=(10, 10))

        self.button_width = button_width
        self.buttons = buttons
        self.set_buttons(buttons)

        self.top.wm_title(title)
        self.allow_exit = allow_exit
        self.top.protocol("WM_DELETE_WINDOW", self.on_closing)

        if (
            self.controller is None and start_mainloop
        ):  # If there's no controller and this is the Tk object, might want to start the mainloop here, or might want
            # to make additional modifications first in a subclass.
            self.top.mainloop()

    @property
    def label(self):
        return self.__label.cget("text")

    @label.setter
    def label(self, val: str):
        self.__label.configure(text=val)

    def set_title(self, newtitle: str):
        self.top.wm_title(newtitle)

    def set_label_text(self, newlabel: str, log_string: Optional[str] = None):
        try:
            self.__label.config(fg=self.tk_format.textcolor, text=newlabel)
        except TclError:
            pass
        if log_string is not None and self.controller is not None:
            self.controller.log(log_string)

    def set_buttons(self, buttons: Dict, button_width: Optional[int] = None):
        self.buttons = buttons
        if button_width is None:
            button_width = self.button_width
        else:
            self.button_width = button_width
        # Sloppy way to check if button_frame already exists and reset it if it does.
        try:
            # pylint: disable = access-member-before-definition
            self.button_frame.destroy()
        except AttributeError:
            pass

        self.button_frame = Frame(self.top, bg=self.tk_format.bg)
        self.button_frame.pack(side=tk.BOTTOM)
        self.tk_buttons = []

        for button in buttons:
            if "ok" in button.lower():
                self.ok_button = Button(
                    self.button_frame, fg=self.tk_format.textcolor, text="OK", command=self.ok, width=self.button_width
                )
                self.ok_button.bind("<Return>", self.ok)
                self.tk_buttons.append(self.ok_button)
                self.ok_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
            elif "yes to all" in button.lower():
                self.yes_to_all_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Yes to all",
                    command=self.yes_to_all,
                    width=self.button_width,
                )
                self.yes_to_all_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.yes_to_all_button)
            elif "yes" in button.lower():
                self.yes_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Yes",
                    bg="light gray",
                    command=self.yes,
                    width=self.button_width,
                )
                self.tk_buttons.append(self.yes_button)
                self.yes_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
            elif "no" in button.lower():
                self.no_button = Button(
                    self.button_frame, fg=self.tk_format.textcolor, text="No", command=self.no, width=self.button_width
                )
                self.no_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.no_button)
            elif "cancel_queue" in button.lower():
                self.cancel_queue_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Cancel",
                    command=self.cancel_queue,
                    width=self.button_width,
                )
                self.cancel_queue_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.cancel_queue_button)
            elif "cancel" in button.lower():
                self.cancel_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Cancel",
                    command=self.cancel,
                    width=self.button_width,
                )
                self.cancel_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.cancel_button)
            elif "retry" in button.lower():
                self.retry_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Retry",
                    command=self.retry,
                    width=self.button_width,
                )
                self.retry_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.retry_button)
            elif "exit" in button.lower():
                self.exit_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Exit",
                    command=self.exit,
                    width=self.button_width,
                )
                self.exit_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.exit_button)
            elif "work offline" in button.lower():
                self.offline_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Work offline",
                    command=self.work_offline,
                    width=self.button_width,
                )
                self.offline_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.offline_button)
            elif "pause" in button.lower():
                self.pause_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Pause",
                    command=self.pause,
                    width=self.button_width,
                )
                self.pause_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.pause_button)
            elif "continue" in button.lower():
                self.continue_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Continue",
                    command=self.cont,
                    width=self.button_width,
                )
                self.continue_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.continue_button)
            elif "close" in button.lower():
                self.close_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Close",
                    command=self.close,
                    width=self.button_width,
                )
                self.close_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.close_button)
            elif "reset" in button.lower():
                self.reset_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Reset",
                    command=self.reset,
                    width=self.button_width,
                )
                self.reset_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.reset_button)
            elif "change ip" in button.lower():
                self.ip_button = Button(
                    self.button_frame,
                    fg=self.tk_format.textcolor,
                    text="Change IP",
                    command=self.change_ip,
                    width=self.button_width,
                )
                self.ip_button.pack(side=tk.LEFT, padx=(10, 10), pady=(10, 10))
                self.tk_buttons.append(self.ip_button)
            for tk_button in self.tk_buttons:
                tk_button.config(
                    fg=self.tk_format.buttontextcolor,
                    highlightbackground=self.tk_format.highlightbackgroundcolor,
                    bg=self.tk_format.buttonbackgroundcolor,
                )

    def on_closing(self):
        if self.allow_exit:
            if self.controller is not None:
                self.controller.unfreeze()
            self.top.destroy()

    def reset(self):
        functions = self.buttons["reset"]
        self.execute(functions, close=False)

    def change_ip(self):
        functions = self.buttons["Change IP"]
        self.execute(functions)

    def close(self):
        if self.controller is not None:
            self.controller.unfreeze()
        self.top.destroy()

    def retry(self):
        self.close()
        functions = self.buttons["retry"]
        self.execute(functions, False)

    def exit(self):
        self.top.destroy()
        utils.exit_func()

    def cont(self):
        functions = self.buttons["continue"]
        self.execute(functions, close=False)

    def pause(self):
        functions = self.buttons["pause"]
        self.execute(functions, close=False)

    def ok(self, event=None):
        # pylint: disable = unused-argument
        functions = self.buttons["ok"]
        self.execute(functions)

    def yes(self):
        functions = self.buttons["yes"]
        self.execute(functions)

    def yes_to_all(self):
        functions = self.buttons["yes to all"]
        self.execute(functions)

    def no(self):
        functions = self.buttons["no"]
        self.execute(functions)

    def cancel(self):
        functions = self.buttons["cancel"]
        self.execute(functions)

    def cancel_queue(self):
        functions = self.buttons["cancel_queue"]
        self.execute(functions, close=False)

    def execute(self, function_info, close=True):
        for function in function_info:
            args = function_info[function]
            function(*args)

        if close:
            self.close()

    def work_offline(self):
        self.close()
        functions = self.buttons["work offline"]
        self.execute(functions, close=False)
