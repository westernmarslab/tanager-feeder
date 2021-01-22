from tanager_feeder.connection_checkers.connection_checker import ConnectionChecker
from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.change_ip_dialog import ChangeIPDialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog


class SpecConnectionChecker(ConnectionChecker):
    def __init__(self, connection_tracker, config_info, controller=None, func=None, args=None):
        if args is None:
            args = []
        super().__init__("spec compy", connection_tracker, config_info, controller, func, args)

    def set_work_offline(self):
        self.connection_tracker.spec_offline = True

    def offline(self):
        return self.connection_tracker.spec_offline

    def lost_dialog(self, buttons):
        try:
            dialog = ErrorDialog(
                controller=self.controller,
                title="Lost Connection",
                label="Error: Lost connection with spec compy.\n\nCheck that you and the spectrometer computer are\nboth connected to the same network.",
                buttons=buttons,
                button_width=15,
            )
        except:
            pass

    # Bring this up if there is no connection with the spectrometer computer
    def no_dialog(self, buttons):
        try:
            dialog = Dialog(
                controller=self.controller,
                title="Not Connected",
                label="Error: No connection with Spec Compy.\n\nCheck that you and the spectrometer computer are\nboth connected to the same network.",
                buttons=buttons,
                button_width=15,
            )
        except Exception as e:
            print(e)
            raise (e)
            pass

    def ask_ip(self):
        dialog = ChangeIPDialog(
            self.connection_tracker,
            title="Change IP",
            label="Enter the IP address for the spectrometer computer.\n\nThe IP address is displayed in the ASD feeder terminal at startup.",
            which_compy="spec compy",
            config_loc=self.config_loc,
        )
