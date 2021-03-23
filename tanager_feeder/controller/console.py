import datetime
from tkinter import RIGHT, Entry, Event, Label, Frame, END, BOTH, BOTTOM, Text, Scrollbar, Y, INSERT
from typing import Optional

from tanager_feeder import utils


class Console:
    def __init__(self, controller: utils.ControllerType):
        self.controller = controller
        self.tk_format = utils.TkFormat(self.controller.config_info)

        self.user_cmds = []
        self.user_cmd_index = 0

        self.console_log = None
        self.console_entry = None
        self.console_frame = None
        self.show()

    def show(self) -> None:
        self.console_frame = Frame(
            self.controller.view_frame,
            bg=self.tk_format.border_color,
            height=200,
            highlightthickness=2,
            highlightcolor=self.tk_format.bg,
        )
        self.console_frame.pack(fill=BOTH, expand=True, padx=(1, 1))
        console_title_label = Label(
            self.console_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.border_color,
            fg="black",
            text="Console",
            font=("Helvetica", 11),
        )
        console_title_label.pack(pady=(5, 5))
        text_frame = Frame(self.console_frame)

        self.some_width = self.controller.control_frame.winfo_width()
        self.console_log = Text(text_frame, width=self.some_width, bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        scrollbar = Scrollbar(text_frame)
        scrollbar.pack(side=RIGHT, fill=Y)
        scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=scrollbar.set)
        self.console_entry = Entry(
            self.console_frame,
            width=self.some_width,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.console_entry.bind("<Return>", self.controller.execute_cmd)
        self.console_entry.bind("<Up>", self.iterate_cmds)
        self.console_entry.bind("<Down>", self.iterate_cmds)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        text_frame.pack(fill=BOTH, expand=True)
        self.console_log.pack(fill=BOTH, expand=True)
        self.console_entry.focus()

    def log(self, info_string: str, newline: Optional[bool] = True) -> None:
        # self.controller.master.update()
        if newline:
            space = self.console_log.winfo_width()
            space = int(space / 8.5)
            current_position = self.console_log.index(INSERT)
            line_char = current_position.split(".")
            current_char = int(line_char[1])
            space = str(space - current_char)
            datestring = ""
            datestringlist = str(datetime.datetime.now()).split(".")[:-1]
            for d in datestringlist:
                datestring = datestring + d

            while info_string[0] == "\n":
                info_string = info_string[1:]

            first_space = int(space) - 15
            if "\n" not in info_string:
                if len(info_string) > first_space:
                    i = first_space - 7
                    while True:
                        if i == 0:
                            info_string = (
                                info_string[0 : int(first_space / 2)] + "\n" + info_string[int(first_space / 2) :]
                            )
                            break
                        if info_string[i] == " ":
                            info_string = info_string[0:i] + "\n" + info_string[i + 1 :]
                            break
                        i -= 1

            first_space = str(first_space)
            if "\n" in info_string:
                lines = info_string.split("\n")
                lines[0] = ("{1:" + first_space + "}{0}").format(datestring, lines[0])
                info_string = "\n".join(lines)
            else:
                info_string = ("{1:" + first_space + "}{0}").format(datestring, info_string)

            if info_string[-2:-1] != "\n" and newline:
                info_string += "\n"

            self.console_log.insert(END, info_string)
            self.console_log.insert(END, "\n")
        else:
            self.console_log.insert(END, info_string)
        self.console_log.see(END)

        # when the focus is on the console entry box, the user can scroll through past commands.
        # these are stored in user_cmds with the index of the most recent command at 0
        # Every time the user enters a command, the user_cmd_index is changed to -1
        self.console_log.see(END)

    # when the focus is on the console entry box, the user can scroll through past commands.
    # these are stored in user_cmds with the index of the most recent command at 0
    # Every time the user enters a command, the user_cmd_index is changed to -1
    def iterate_cmds(self, keypress_event: Event) -> None:
        if (
            keypress_event.keycode == 111 or keypress_event.keycode == 38
        ):  # up arrows on linux and windows, respectively

            if len(self.user_cmds) > self.user_cmd_index + 1 and len(self.user_cmds) > 0:
                self.user_cmd_index = self.user_cmd_index + 1
                last = self.user_cmds[self.user_cmd_index]
                self.console_entry.delete(0, "end")
                self.console_entry.insert(0, last)

        elif (
            keypress_event.keycode == 116 or keypress_event.keycode == 40
        ):  # down arrow on linux and windows, respectively
            if self.user_cmd_index > 0:
                self.user_cmd_index = self.user_cmd_index - 1
                next_cmd = self.user_cmds[self.user_cmd_index]
                self.console_entry.delete(0, "end")
                self.console_entry.insert(0, next_cmd)

    def next_cmd(self) -> str:
        command: str = self.console_entry.get()
        self.user_cmds.insert(0, command)
        self.user_cmd_index = -1
        if command != "end file":
            self.console_log.insert(END, ">>> " + command + "\n")
        self.console_entry.delete(0, "end")
        return command
