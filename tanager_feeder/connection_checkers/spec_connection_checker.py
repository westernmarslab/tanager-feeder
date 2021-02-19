from typing import Dict, List, Optional

from tanager_feeder.connection_checkers.connection_checker import ConnectionChecker
from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.change_ip_dialog import ChangeIPDialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.utils import CompyTypes, ConfigInfo, ConnectionTracker


class SpecConnectionChecker(ConnectionChecker):
    def __init__(
        self,
        connection_tracker: ConnectionTracker,
        config_info: ConfigInfo,
        controller=None,
        func=None,
        args: Optional[List] = None,
    ):
        if args is None:
            args = []
        super().__init__(CompyTypes.SPEC_COMPY.value, connection_tracker, config_info, controller, func, args)

    def set_work_offline(self):
        self.connection_tracker.spec_offline = True

    def offline(self):
        return self.connection_tracker.spec_offline

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
            controller=self.controller,
            title="Not Connected",
            label="Error: No connection with Spec Compy.\n\n"
            "Check that you and the spectrometer computer are\n"
            "both connected to the same network.",
            buttons=buttons,
            button_width=15,
        )

    def ask_ip(self):
        ChangeIPDialog(
            self.connection_tracker,
            title="Change IP",
            label="Enter the IP address for the spectrometer computer.\n\n"
            "The IP address is displayed in the ASD feeder terminal at startup.",
            which_compy=CompyTypes.SPEC_COMPY.value,
            config_loc=self.config_loc,
        )
