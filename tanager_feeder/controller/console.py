class Console():
    def __init__(self, master, viewframe):
        # ************************Console********************************
        self.console_frame = Frame(
            view_frame, bg=self.border_color, height=200, highlightthickness=2, highlightcolor=self.bg
        )
        self.console_frame.pack(fill=BOTH, expand=True, padx=(1, 1))
        self.console_title_label = Label(
            self.console_frame,
            padx=self.padx,
            pady=self.pady,
            bg=self.border_color,
            fg="black",
            text="Console",
            font=("Helvetica", 11),
        )
        self.console_title_label.pack(pady=(5, 5))
        self.text_frame = Frame(self.console_frame)
        self.scrollbar = Scrollbar(self.text_frame)
        self.some_width = self.control_frame.winfo_width()
        self.console_log = Text(self.text_frame, width=self.some_width, bg=self.bg, fg=self.textcolor)
        self.scrollbar.pack(side=RIGHT, fill=Y)

        self.scrollbar.config(command=self.console_log.yview)
        self.console_log.configure(yscrollcommand=self.scrollbar.set)
        self.console_entry = Entry(
            self.console_frame,
            width=self.some_width,
            bd=self.bd,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.console_entry.bind("<Return>", self.execute_cmd)
        self.console_entry.bind("<Up>", self.iterate_cmds)
        self.console_entry.bind("<Down>", self.iterate_cmds)
        self.console_entry.pack(fill=BOTH, side=BOTTOM)
        self.text_frame.pack(fill=BOTH, expand=True)
        self.console_log.pack(fill=BOTH, expand=True)
        self.console_entry.focus()
    def log(self, info_string):
        self.master.update()
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