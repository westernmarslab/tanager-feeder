from typing import Dict, List, Optional

from tanager_feeder.utils import ConfigInfo, ConnectionManager, exit_func


class ConnectionChecker:
    def __init__(
        self,
        connection_manager: ConnectionManager,
        config_info: ConfigInfo,
        controller,
        func,
        args: Optional[List],
    ):
        self.config_loc: str = config_info.local_config_loc
        self.connection_manager = connection_manager
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
                self.check_connection: [4],
            },
            "work offline": {self.set_work_offline: [], self.func: self.args},
            "Change IP": {self.ask_ip: []},
        }
        self.no_dialog(buttons)

    def check_connection(self, timeout: int = 3):
        raise NotImplementedError

    def release(self):
        self.busy = False

    def lost_dialog(self, buttons: Dict):
        raise NotImplementedError

    def no_dialog(self, buttons: Dict):
        raise NotImplementedError

    def set_work_offline(self):
        raise NotImplementedError

    def ask_ip(self):
        raise NotImplementedError
