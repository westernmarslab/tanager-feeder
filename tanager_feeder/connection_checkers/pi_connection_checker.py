from tanager_feeder.connection_checkers.connection_checker import ConnectionChecker
from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.change_ip_dialog import ChangeIPDialog


class PiConnectionChecker(ConnectionChecker):
    def __init__(self, connection_tracker, config_info, controller=None, func=None, args=None):
        if args is None:
            args = []
        super().__init__('pi', connection_tracker, config_info, controller, func, args)

    def set_work_offline(self):
        self.connection_tracker.pi_offline = True

    def offline(self):
        return self.connection_tracker.pi_offline

    def lost_dialog(self, buttons):
        try:
            dialog = ErrorDialog(controller=self.controller, title='Lost Connection',
                                 label='Error: Lost connection with Raspberry Pi.\n\nCheck you and the Raspberry Pi are\nboth on the correct WiFi network and the\nPiShare folder is mounted on your computer',
                                 buttons=buttons, button_width=15)
        except:
            pass

    def no_dialog(self, buttons):
        try:
            dialog = Dialog(controller=self.controller, title='Not Connected',
                            label='Error: Raspberry Pi not connected.\n\nCheck you and the Raspberry Pi are\nboth connected to the same network.',
                            buttons=buttons, button_width=15)
        except:
            pass

    def ask_ip(self):
        dialog = ChangeIPDialog(self.connection_tracker, title='Change IP',
                                label='Enter the IP address for the raspberry pi.\n\n.', which_compy='pi',
                                config_loc=self.config_loc)
