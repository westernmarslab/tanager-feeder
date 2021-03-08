from tkinter import Frame, Label, Entry, LEFT

from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.utils import CompyTypes, ConnectionManager


class ChangeIPDialog(Dialog):
    def __init__(
        self, connection_manager: ConnectionManager, title: str, label: str, which_compy: str, config_loc: str
    ):
        buttons = {
            "ok": {
                self.ok: [],
            },
            "cancel": {
                self.cancel: [],
            },
        }
        super().__init__(None, title, label, buttons, allow_exit=False, start_mainloop=False)
        self.connection_manager = connection_manager

        self.entry_frame = Frame(self.top, bg=self.tk_format.bg)
        self.entry_frame.pack(pady=(10, 20))

        frame = Frame(self.entry_frame, bg=self.tk_format.bg)
        frame.pack(pady=(5, 5))
        change_label = Label(frame, text="IP address: ", fg=self.tk_format.textcolor, bg=self.tk_format.bg)
        change_label.pack(side=LEFT)
        self.ip_entry = Entry(
            frame,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        if which_compy == CompyTypes.SPEC_COMPY.value:
            print("spec ip")
            print(self.connection_manager.spec_ip)
            self.ip_entry.insert(0, self.connection_manager.spec_ip)
        else:
            self.ip_entry.insert(0, self.connection_manager.pi_ip)
        self.ip_entry.pack(side=LEFT)
        self.which_compy = which_compy
        self.config_loc = config_loc

        self.top.mainloop()

    def ok(self):
        if self.which_compy == CompyTypes.SPEC_COMPY.value:
            self.connection_manager.spec_ip = self.ip_entry.get()
            print(self.connection_manager.spec_ip)

        elif self.which_compy == CompyTypes.PI.value:
            self.connection_manager.pi_ip = self.ip_entry.get()

        with open(self.config_loc + "ip_addresses.txt", "w+") as f:
            if self.connection_manager.spec_ip != "":
                print("writing ip! ")
                print("spec ip")
                print(self.connection_manager.spec_ip)
                f.write(self.connection_manager.spec_ip + "\n")
            else:
                f.write("spec_compy_ip\n")
            if self.connection_manager.spec_ip != "":
                print("writing pi_pi")
                print(self.connection_manager.pi_ip)
                f.write(self.connection_manager.pi_ip)
            else:
                f.write("raspberrypi")

        self.top.destroy()

    def cancel(self):
        self.top.destroy()
