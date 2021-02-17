from tkinter import ttk, Frame
from typing import Dict, Optional

from tanager_feeder.dialogs.dialog import Dialog


class WaitDialog(Dialog):
    def __init__(self, controller, title="Working...", label="Working...", buttons: Optional[Dict] = None):
        if buttons is None:
            buttons = {}
        super().__init__(controller, title, label, buttons, width=400, height=150, allow_exit=False)

        self.frame = Frame(self.top, bg=self.tk_format.bg, width=200, height=30)
        self.frame.pack()

        style = ttk.Style()
        style.configure("Horizontal.TProgressbar", background="white")
        self.pbar = ttk.Progressbar(self.frame, mode="indeterminate", name="pb2", style="Horizontal.TProgressbar")
        self.pbar.start([10])
        self.pbar.pack(padx=(10, 10), pady=(10, 10))

    def interrupt(self, label: str):
        self.set_label_text(label)
        self.pbar.stop()
        self.set_buttons({"ok": {}})

    def reset(self, title: str = "Working...", label: str = "Working...", buttons: Optional[Dict] = None):
        if buttons is None:
            buttons = {}
        self.set_label_text(label)
        self.set_buttons(buttons)
        self.set_title(title)
        self.pbar.start([10])
