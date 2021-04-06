import time
from typing import Dict, List, Optional

from tanager_feeder.connection_checkers.connection_checker import ConnectionChecker
from tanager_feeder.dialogs.dialog import Dialog
from tanager_feeder.dialogs.error_dialog import ErrorDialog
from tanager_feeder.dialogs.change_ip_dialog import ChangeIPDialog

from tanager_feeder.utils import CompyTypes, ConfigInfo, ConnectionManager


class PiConnectionChecker(ConnectionChecker):
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
        self.connection_manager.pi_offline = True

    def offline(self):
        return self.connection_manager.pi_offline

    def lost_dialog(self, buttons: Dict):
        ErrorDialog(
            controller=self.controller,
            title="Lost Connection",
            label="Error: Lost connection with Raspberry Pi.\n\n"
            "Check you and the Raspberry Pi are\n"
            "both connected to the same network.",
            buttons=buttons,
            button_width=15,
        )

    def no_dialog(self, buttons: Dict):
        try:
            Dialog(
                controller=self.controller,
                title="Not Connected",
                label="Error: Raspberry Pi not connected.\n\n"
                "Check you and the Raspberry Pi are\n"
                "both connected to the same network.",
                buttons=buttons,
                button_width=15,
            )
        except RuntimeError:
            pass

    def ask_ip(self):
        ChangeIPDialog(
            self.connection_manager,
            title="Change IP",
            label="Enter the IP address for the raspberry pi.\n\n.",
            which_compy=CompyTypes.PI.value,
            config_loc=self.config_loc,
        )

    def check_connection(self, timeout: int = 3, attempts: int = 1):
        attempt = 1
        connected = self.connection_manager.send_to_pi("test", connect_timeout=timeout)

        if not connected and attempt >= attempts:
            self.alert_not_connected()
        elif not connected:
            print("Pi not connected. Retrying.")
            time.sleep(2)
            self.check_connection(timeout, attempts - 1)
        else:
            self.func(*self.args)

        return connected
