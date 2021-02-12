import socket
from typing import Dict, List, Optional

from tanager_tcp import TanagerClient
from tanager_feeder.utils import CompyTypes, ConfigInfo, ConnectionTracker, exit_func


class ConnectionChecker:
    def __init__(
        self,
        which_compy: str,
        connection_tracker: ConnectionTracker,
        config_info: ConfigInfo,
        controller,
        func,
        args: Optional[List],
    ):
        self.which_compy = which_compy
        self.config_loc: str = config_info.local_config_loc
        self.connection_tracker = connection_tracker
        self.controller = controller
        self.func = func
        self.busy: bool = False
        self.args = args

    def alert_lost_connection(self):
        buttons = {
            "retry": {self.release: [], self.check_connection: [6]},
            "work offline": {self.set_work_offline: []},
            "exit": {exit_func: []},
        }
        self.lost_dialog(buttons)

    def alert_not_connected(self):
        buttons = {
            "retry": {
                self.release: [],
                self.check_connection: [6],
            },
            "work offline": {self.set_work_offline: [], self.func: self.args},
            "Change IP": {self.ask_ip: []},
        }
        self.no_dialog(buttons)

    def check_connection(self, timeout: int = 3):
        if self.which_compy == "spec compy":
            server_ip = self.connection_tracker.spec_ip
            listening_port = self.connection_tracker.SPEC_PORT
        else:
            server_ip = self.connection_tracker.pi_ip
            listening_port = self.connection_tracker.PI_PORT

        connected = False
        try:
            TanagerClient((server_ip, 12345), "test", listening_port, timeout=timeout)
            # TODO: separate into single client instantiation, then send a message at each check.
            if self.which_compy == CompyTypes.SPEC_COMPY.value:
                self.connection_tracker.spec_offline = False
            else:
                self.connection_tracker.pi_offline = False
            connected = True
        except socket.timeout:
            self.alert_not_connected()

        if connected:
            self.func(*self.args)

        return connected

    def release(self):
        self.busy = False

    def lost_dialog(self, buttons: Dict):
        pass

    def no_dialog(self, buttons: Dict):
        pass

    def get_offline(self):
        pass

    def set_work_offline(self):
        pass

    def ask_ip(self):
        pass
