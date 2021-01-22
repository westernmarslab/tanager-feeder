from tanager_feeder.dialogs.dialog import Dialog


class CustomColorDialog(Dialog):
    def __init__(self, controller, func, color_variable, title="Custom Color"):
        super().__init__(
            controller, label="Enter custom hue: ", title=title, buttons={"ok": {self.ok: []}}, button_width=15
        )
        #         self.hue_label=Label(self.top, text='Hue: ')
        #         self.hue_label.pack(side=LEFT, padx=(10,10))
        self.hue_entry = Entry(
            self.top,
            width=10,
            bg=self.entry_background,
            selectbackground=self.selectbackground,
            selectforeground=self.selectforeground,
        )
        self.hue_entry.pack(padx=(10, 10))
        self.func = func

    def ok(self):
        try:
            color_variable = int(self.hue_entry.get())
            if color_variable < 0 or color_variable > 359:
                raise Exception()
        except:
            dialog = ErrorDialog(self.controller, "Error", "Error: Invalid custom hue.\n\nEnter a number 0-359.")
            return
        self.func(int(self.hue_entry.get()))
        self.top.destroy()
