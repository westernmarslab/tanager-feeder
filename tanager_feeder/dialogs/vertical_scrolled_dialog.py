class VerticalScrolledDialog(Dialog):
    def __init__(self, controller, title, label, buttons={}, button_width=None, min_height=810, width=370, height=820):
        screen_height = controller.master.winfo_screenheight()
        if height > screen_height - 150:
            height = screen_height - 150

        super().__init__(controller, title, label, buttons, button_width=button_width, width=width, height=height)

        self.frame = VerticalScrolledFrame(controller, self.top, width=width, min_height=min_height, height=height)
        self.frame.config(height=height)
        self.frame.canvas.config(height=height)
        self.frame.pack()
        self.interior = self.frame.interior

    def update(self):
        self.frame.update(controller_resize=False)
