from tanager_feeder.dialogs.dialog import Dialog

class ErrorDialog(Dialog):
    def __init__(self, controller, title='Error', label='Error!', buttons={'ok': {}}, listener=None, allow_exit=False,
                 info_string=None, topmost=True, button_width=30, width=None, height=None):

        self.listener = None
        if info_string == None:
            self.info_string = label + '\n'
        else:
            self.info_string = info_string
        if width == None or height == None:
            super().__init__(controller, title, label, buttons, allow_exit=False, info_string=None,
                             button_width=button_width)  # self.info_string)
        else:
            super().__init__(controller, title, label, buttons, allow_exit=False, info_string=None,
                             button_width=button_width, width=width, height=height)
        if topmost == True:
            try:
                self.top.attributes("-topmost", True)
            except(Exception):
                print(str(Exception))