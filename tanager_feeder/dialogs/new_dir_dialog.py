from tkinter import Entry
from tanager_feeder.dialogs.dialog import Dialog


class NewDirDialog(Dialog):
    def __init__(self, controller, fexplorer, label="New directory name: ", title="New Directoy"):
        super().__init__(
            controller, label=label, title=title, buttons={"ok": {self.get: []}, "cancel": {}}, button_width=15
        )
        self.dir_entry = Entry(
            self.top,
            width=40,
            bg=self.tk_format.entry_background,
            selectbackground=self.tk_format.selectbackground,
            selectforeground=self.tk_format.selectforeground,
        )
        self.dir_entry.pack(padx=(10, 10))
        self.listener = self.controller.spec_listener
        self.fexplorer = fexplorer

    def get(self):
        subdir = self.dir_entry.get()
        if subdir[0:3] != "C:\\":
            self.fexplorer.mkdir(self.fexplorer.current_parent + "\\" + subdir)
        else:
            self.fexplorer.mkdir(subdir)
