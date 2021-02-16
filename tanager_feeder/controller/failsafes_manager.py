from tkinter import Entry, Button, Label, Checkbutton, Toplevel, Frame, BOTH


class FailsafesManager():
    def __init__(self, master):
        self.settings_top = Toplevel(master)
        self.settings_top.wm_title("Failsafe Settings")
        self.settings_frame = Frame(self.settings_top, bg=self.bg, pady=2 * self.pady, padx=15)
        self.settings_frame.pack()

        self.failsafe_title_frame = Frame(self.settings_frame, bg=self.bg)
        self.failsafe_title_frame.pack(pady=(10, 0), fill=X, expand=True)
        self.failsafe_label0 = Label(
            self.failsafe_title_frame,
            fg=self.textcolor,
            text="Failsafes:                                                                      ",
            bg=self.bg,
        )
        self.failsafe_label0.pack(side=LEFT)

        self.failsafe_frame = Frame(self.settings_frame, bg=self.bg, pady=self.pady)
        self.failsafe_frame.pack(fill=BOTH, expand=True, padx=(10, 10))

        self.wr_failsafe_check_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wr_failsafe_check_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.wrfailsafe_check = Checkbutton(
            self.wr_failsafe_check_frame,
            fg=self.textcolor,
            text="Prompt if no white reference has been taken.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.wrfailsafe,
            selectcolor=self.check_bg,
        )
        self.wrfailsafe_check.pack(side=LEFT)
        if self.wrfailsafe.get():
            self.wrfailsafe_check.select()

        self.wr_timeout_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wr_timeout_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.wr_timeout_label = Label(self.wr_timeout_frame, fg=self.textcolor, text="Timeout (minutes):", bg=self.bg)
        self.wr_timeout_label.pack(side=LEFT, padx=(20, 0))
        self.wr_timeout_entry = Entry(
            self.wr_timeout_frame,
            bd=self.bd,
            width=10,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.wr_timeout_entry.pack(side=LEFT, padx=(0, 20))
        self.wr_timeout_entry.insert(0, "8")

        self.optfailsafe_check_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.optfailsafe_check_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.optfailsafe_check = Checkbutton(
            self.optfailsafe_check_frame,
            fg=self.textcolor,
            text="Prompt if the instrument has not been optimized.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            selectcolor=self.check_bg,
            variable=self.optfailsafe,
        )
        self.optfailsafe_check.pack(side=LEFT)
        if self.optfailsafe.get():
            self.optfailsafe_check.select()

        self.opt_timeout_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.opt_timeout_frame.pack(pady=self.pady, fill=X, expand=True, padx=(20, 5))
        self.opt_timeout_label = Label(self.opt_timeout_frame, fg=self.textcolor, text="Timeout (minutes):", bg=self.bg)
        self.opt_timeout_label.pack(side=LEFT, padx=(20, 0))
        self.opt_timeout_entry = Entry(
            self.opt_timeout_frame,
            bd=self.bd,
            width=10,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.opt_timeout_entry.pack(side=LEFT, padx=(0, 20))
        self.opt_timeout_entry.insert(0, "60")
        self.filler_label = Label(self.opt_timeout_frame, bg=self.bg, fg=self.textcolor, text="              ")
        self.filler_label.pack(side=LEFT)

        self.angles_failsafe_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.angles_failsafe_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.angles_failsafe_check = Checkbutton(
            self.angles_failsafe_frame,
            fg=self.textcolor,
            text="Check validity of emission and incidence angles.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            selectcolor=self.check_bg,
            variable=self.angles_failsafe,
        )
        # self.angles_failsafe_check.pack(pady=(6,5),side=LEFT,padx=(0,20))
        if self.angles_failsafe.get():
            self.angles_failsafe_check.select()

        self.label_failsafe_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.label_failsafe_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.label_failsafe_check = Checkbutton(
            self.label_failsafe_frame,
            fg=self.textcolor,
            text="Require a label for each spectrum.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            selectcolor=self.check_bg,
            variable=self.labelfailsafe,
        )
        self.label_failsafe_check.pack(pady=(6, 5), side=LEFT, padx=(0, 20))
        if self.labelfailsafe.get():
            self.label_failsafe_check.select()

        self.wr_angles_failsafe_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wr_angles_failsafe_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.wr_angles_failsafe_check = Checkbutton(
            self.wr_angles_failsafe_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text="Require a new white reference at each viewing geometry             ",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.wr_angles_failsafe,
        )
        self.wr_angles_failsafe_check.pack(pady=(6, 5), side=LEFT)
        if self.wr_angles_failsafe.get():
            self.wr_angles_failsafe_check.select()

        self.wrap_frame = Frame(self.failsafe_frame, bg=self.bg)
        self.wrap_frame.pack(pady=self.pady, padx=(20, 5), fill=X, expand=True)
        self.anglechangefailsafe_check = Checkbutton(
            self.wrap_frame,
            selectcolor=self.check_bg,
            fg=self.textcolor,
            text="Remind me to check the goniometer if the viewing geometry changes.",
            bg=self.bg,
            pady=self.pady,
            highlightthickness=0,
            variable=self.anglechangefailsafe,
        )
        # self.anglechangefailsafe_check.pack(pady=(6,5),side=LEFT)#side=LEFT, pady=self.pady)
        # if self.anglechangefailsafe.get():
        #   self.anglechangefailsafe_check.select()

        self.failsafes_ok_button = Button(self.failsafe_frame, text="Ok", command=self.settings_top.destroy)
        self.failsafes_ok_button.config(
            fg=self.buttontextcolor,
            highlightbackground=self.highlightbackgroundcolor,
            bg=self.buttonbackgroundcolor,
            width=15,
        )
        self.failsafes_ok_button.pack(pady=self.pady)
        self.settings_top.resizable(False, False)