from typing import Dict, List, Optional

from tanager_feeder.connection_checkers.connection_checker import ConnectionChecker
from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.change_ip_dialog import ChangeIPDialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.utils import CompyTypes, ConfigInfo, ConnectionManager


class SpecConnectionChecker(ConnectionChecker):
    def __init__(
        self,
        connection_manager: ConnectionManager,
        config_info: ConfigInfo,
        controller=None,
        func=None,
        args: Optional[List] = None,
    ):
        if args is None:
            args = []
        super().__init__(connection_manager, config_info, controller, func, args)

    def set_work_offline(self):
        self.connection_manager.spec_offline = True

    def offline(self):
        return self.connection_manager.spec_offline

    def lost_dialog(self, buttons: Dict):
        ErrorDialog(
            controller=self.controller,
            title="Lost Connection",
            label="Error: Lost connection with spec compy.\n\nCheck that you and the spectrometer computer are\n"
            "both connected to the same network.",
            buttons=buttons,
            button_width=15,
        )

    # Bring this up if there is no connection with the spectrometer computer
    def no_dialog(self, buttons: Dict):
        Dialog(
            controller=None,
            title="Not Connected",
            label="Error: No connection with Spec Compy.\n\n"
            "Check that you and the spectrometer computer are\n"
            "both connected to the same network.",
            buttons=buttons,
            button_width=15,
        )

    def ask_ip(self):
        ChangeIPDialog(
            self.connection_manager,
            title="Change IP",
            label="Enter the IP address for the spectrometer computer.\n\n"
            "The IP address is displayed in the ASD feeder terminal at startup.",
            which_compy=CompyTypes.SPEC_COMPY.value,
            config_loc=self.config_loc,
        )

    def check_connection(self, timeout: int = 3, show_dialog: bool = True):
        if self.connection_manager.spec_offline:
            connected = self.connection_manager.connect_spec(timeout)
        else:
            connected = self.connection_manager.send_to_spec("test")

        if connected:
            self.func(*self.args)
        elif show_dialog:
            self.alert_not_connected()

        return connected
