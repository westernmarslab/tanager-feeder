import datetime
from tkinter import RIGHT, Entry, Label, Frame, END, BOTH, BOTTOM, Text, Scrollbar, Y
from tanager_feeder import utils


class Console:
    def __init__(self, controller):
        self.controller = controller
        self.tk_format = utils.TkFormat(self.controller.config_info)
        self.console_frame = Frame(
            self.controller.view_frame, bg=self.tk_format.border_color, height=200, highlightthickness=2, highlightcolor=self.tk_format.bg
        )
        self.console_frame.pack(fill=BOTH, expand=True, padx=(1, 1))
        self.console_title_label = Label(
            self.console_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.border_color,
            fg="black",
            text="Console",
            font=("Helvetica", 11),
        )
        self.console_title_label.pack(pady=(5, 5))
        self.text_frame = Frame(self.console_frame)
        from tkinter import Scrollbar, Text, BOTTOM, Y
        self.scrollbar = Scrollbar(self.text_frame)
        self.some_width = self.controller.control_frame.winfo_width()
        self.console_log = Text(self.text_frame, width=self.some_width, bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry = Entry(
            self.console_frame,
            width=self.some_width,
            bd=self.tk_format.bd,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.console_entry.bind("<Return>", self.controller.execute_cmd)
        # self.console_entry.bind("<Up>", self.iterate_cmds)
        # self.console_entry.bind("<Down>", self.iterate_cmds)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.console_log.pack(fill=BOTH, expand=True)
        self.console_entry.focus()

    def foo(self, controller):
        self.user_cmds = []
        self.user_cmd_index = 0
        self.controller = controller
        self.tk_format = utils.TkFormat(self.controller.config_info)

        self.console_log = None
        self.console_entry = None
        self.show()

    def show(self):
        console_frame = Frame(
            self.controller.view_frame,
            bg=self.tk_format.border_color,
            height=200,
            highlightthickness=2,
            highlightcolor=self.tk_format.bg,
        )
        console_frame.pack(fill=BOTH, expand=True, padx=(1, 1))
        console_title_label = Label(
            console_frame,
            padx=self.tk_format.padx,
            pady=self.tk_format.pady,
            bg=self.tk_format.border_color,
            fg="black",
            text="Console",
            font=("Helvetica", 11),
        )
        console_title_label.pack(pady=(5, 5))
        text_frame = Frame(console_frame)
        scrollbar = Scrollbar(text_frame)
        some_width = self.controller.control_frame.winfo_width()
        self.console_log = Text(text_frame, width=some_width, bg=self.tk_format.bg, fg=self.tk_format.textcolor)
        scrollbar.pack(side=RIGHT, fill=Y)

        scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=scrollbar.set)
        self.console_entry = Entry(
            console_frame,
            width=some_width,
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

    def log(self, info_string):
        self.controller.master.update()
        space = self.console_log.winfo_width()
        space = str(int(space / 8.5))
        if int(space) < 20:
            space = str(20)
        datestring = ""
        datestringlist = str(datetime.datetime.now()).split(".")[:-1]
        for d in datestringlist:
            datestring = datestring + d

        while info_string[0] == "\n":
            info_string = info_string[1:]

        if "\n" in info_string:
            lines = info_string.split("\n")

            lines[0] = ("{1:" + space + "}{0}").format(datestring, lines[0])
            for i in range(len(lines)):
                if i == 0:
                    continue
                else:
                    lines[i] = ("{1:" + space + "}{0}").format("", lines[i])
            info_string = "\n".join(lines)
        else:
            info_string = ("{1:" + space + "}{0}").format(datestring, info_string)

        if info_string[-2:-1] != "\n":
            info_string += "\n"

        self.console_log.insert(END, info_string + "\n")
        self.console_log.see(END)

    # when the focus is on the console entry box, the user can scroll through past commands.
    # these are stored in user_cmds with the index of the most recent command at 0
    # Every time the user enters a command, the user_cmd_index is changed to -1
    def iterate_cmds(self, keypress_event):
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

    def next_cmd(self):
        command = self.console_entry.get()
        self.user_cmds.insert(0, command)
        self.user_cmd_index = -1
        if command != "end file":
            self.console_log.insert(END, ">>> " + command + "\n")
        self.console_entry.delete(0, "end")
        return command
