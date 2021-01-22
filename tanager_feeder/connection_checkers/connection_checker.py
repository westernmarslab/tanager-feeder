import traceback

from tanager_tcp import TanagerClient


class ConnectionChecker:
    def __init__(self, which_compy, connection_tracker, config_info, controller, func, args):
        self.which_compy = which_compy
        self.config_loc = config_info.local_config_loc
        self.connection_tracker = connection_tracker
        self.controller = controller
        self.func = func
        self.busy = False
        self.args = args

    def alert_lost_connection(self):
        buttons = {
            "retry": {self.release: [], self.check_connection: [6]},
            "work offline": {self.set_work_offline: []},
            "exit": {exit_func: []},
        }
        self.lost_dialog(buttons)

    def change_ip(self):
        pass

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

    def check_connection(self, timeout=3):
        if self.which_compy == "spec compy":
            server_ip = self.connection_tracker.spec_ip
            listening_port = self.connection_tracker.SPEC_PORT
        else:
            server_ip = self.connection_tracker.pi_ip
            listening_port = self.connection_tracker.PI_PORT
        connected = False

        try:
            client = TanagerClient((server_ip, 12345), "test", listening_port, timeout=timeout)
            if self.which_compy == "spec compy":
                self.connection_tracker.spec_offline = False
            else:
                self.connection_tracker.pi_offline = False
            self.func(*self.args)
            connected = True
        except Exception as e:
            traceback.print_exc()
            self.alert_not_connected()

        if connected:
            self.func(*self.args)

        return connected

    def release(self):
        self.busy = False

    def lost_dialog(self):
        pass

    def no_dialog(self):
        pass

    def get_offline(self):
        pass

    def set_work_offline(self):
        pass
