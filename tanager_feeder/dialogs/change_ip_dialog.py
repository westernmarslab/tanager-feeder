from tanager_feeder.dialogs.dialog import Dialog
from tkinter import Frame, Label, Entry, LEFT


class ChangeIPDialog(Dialog):
    def __init__(self, connection_tracker, title, label, which_compy, config_loc):
        buttons = {
            "ok": {
                self.ok: [],
            },
            "cancel": {
                self.cancel: [],
            },
        }
        super().__init__(None, title, label, buttons, allow_exit=False, start_mainloop=False)
        self.connection_tracker = connection_tracker

        self.entry_frame = Frame(self.top, bg=self.bg)
        self.entry_frame.pack(pady=(10, 20))

        frame = Frame(self.entry_frame, bg=self.bg)
        frame.pack(pady=(5, 5))
        change_label = Label(frame, text="IP address: ", fg=self.textcolor, bg=self.bg)
        change_label.pack(side=LEFT)
        self.ip_entry = Entry(
            frame,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        if which_compy == "spec compy":
            self.ip_entry.insert(0, self.connection_tracker.spec_ip)
        else:
            print("CON TRACK PI IP")
            print(self.connection_tracker.pi_ip)
            self.ip_entry.insert(0, self.connection_tracker.pi_ip)
        self.ip_entry.pack(side=LEFT)
        self.which_compy = which_compy
        self.config_loc = config_loc

        self.top.mainloop()

    def ok(self):
        print("CHANGING IP!")
        if self.which_compy == "spec compy":
            self.connection_tracker.spec_ip = self.ip_entry.get()

        elif self.which_compy == "pi":
            print("CHANGING CONNECTION_TRACKER_PI_IP")
            self.connection_tracker.pi_ip = self.ip_entry.get()

        with open(self.config_loc + "ip_addresses.txt", "w+") as f:
            print(self.config_loc)
            if self.connection_tracker.spec_ip != "":
                f.write(self.connection_tracker.spec_ip + "\n")
            else:
                f.write("spec_compy_ip\n")
            if self.connection_tracker.spec_ip != "":
                f.write(self.connection_tracker.pi_ip)
            else:
                f.write("raspberrypi")

        self.top.destroy()

    def cancel(self):
        self.top.destroy()