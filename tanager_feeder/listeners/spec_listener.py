from threading import Thread
import time

from tanager_tcp.tanager_server import TanagerServer

from tanager_feeder.listeners.listener import Listener
from tanager_feeder import utils
from tanager_feeder.connection_checkers.spec_connection_checker import SpecConnectionChecker
from tanager_feeder.dialogs.error_dialog import ErrorDialog


class SpecListener(Listener):
    def __init__(self, connection_manager: utils.ConnectionManager, config_info: utils.ConfigInfo):
        connection_checker = SpecConnectionChecker(connection_manager, config_info, func=self.listen)
        super().__init__(connection_manager, connection_checker)
        self.unexpected_files = []
        self.wait_for_unexpected_count = 0
        self.alert_lostconnection = True
        self.new_dialogs = True
        self.local_server = TanagerServer(port=self.connection_manager.LISTEN_FOR_SPEC_PORT)
        if not self.connection_manager.spec_offline:
            self.set_control_address()
        thread = Thread(target=self.local_server.listen)
        thread.start()

        self.locked = False

    def set_control_address(self):
        self.connection_manager.send_to_spec(
            "setcontrolserveraddress&"
            + self.local_server.server_address[0]
            + "&"
            + str(self.connection_manager.LISTEN_FOR_SPEC_PORT)
        )

    def run(self):
        i = 0
        while True:
            if not self.connection_manager.spec_offline and i % 100 == 0 and not self.controller.restarting_spec_compy:
                if len(self.controller.queue) > 0:
                    attempts = 5
                else:
                    attempts = 1
                self.connection_checker.check_connection(timeout=8, attempts=attempts)
            else:
                self.listen()
            i += 1
            time.sleep(utils.INTERVAL)

    def listen(self):
        while len(self.local_server.queue) > 0:
            message = self.local_server.queue.pop(0)
            cmd, params = utils.decrypt(message)

            if "lostconnection" not in cmd:
                print("Spec read command: " + cmd)

            if cmd == "listdir":
                # RemoteDirectoryWorker in wait_for_contents is waiting for a file that contains a list of the contents
                # of a given folder on the spec compy. This file will have an encrypted version of the parent
                # directory's path in its title e.g. listdir&R=+RiceData+Kathleen+spectral_data
                self.queue.append(message)
            elif "spec_data" in cmd:
                found = False
                for item in self.queue:
                    if "spec_data" in item:
                        found = True
                        item["spec_data"] = item["spec_data"] + "&".join(params)
                if not found:
                    self.queue.append({"spec_data": "&".join(params)})

                if cmd == "spec_data_final":
                    self.queue.append("spec_data_transferred")
            elif cmd == "savedfile":
                self.queue.append(cmd)

            elif cmd == "restarting":
                self.queue.append(cmd)

            elif "log_data" in cmd:
                found = False
                for item in self.queue:
                    if "log_data" in item:
                        found = True
                        item["log_data"] = item["log_data"] + "&".join(params)
                if not found:
                    self.queue.append({"log_data": "&".join(params)})

                if cmd == "log_data_final":
                    self.queue.append("log_data_transferred")

            elif "listcontents" in cmd:
                self.queue.append(message)

            elif "lostconnection" in cmd and not self.controller.restarting_spec_compy:
                if self.alert_lostconnection:
                    self.alert_lostconnection = False
                    time.sleep(4)
                    self.controller.freeze()
                    buttons = {
                        "retry": {
                            self.set_alert_lostconnection: [True],
                        },
                        "work offline": {},
                        "exit": {utils.exit_func: []},
                    }
                    ErrorDialog(
                        controller=self.controller,
                        title="Lost Connection",
                        label="Error: RS3 has no connection with the spectrometer.\nCheck that the spectrometer is"
                        " on.\n\nNote that RS3 can take some time to connect to the spectrometer.\nBe patient"
                        " and wait for the dot at the lower right of RS3 to turn green.",
                        buttons=buttons,
                        button_width=15,
                        width=600,
                    )

            elif "unexpectedfile" in cmd and not self.controller.restarting_spec_compy:
                if self.new_dialogs:
                    ErrorDialog(
                        self.controller,
                        title="Untracked Files",
                        label="There is an untracked file in the data directory.\nDoes this belong here?\n\n"
                        + params[0],
                    )
                    for param in params:
                        print(param)
                        self.controller.log(f"Warning: Unexpected file(s) in the data directory:\n{params}")
                else:
                    for param in params:
                        print(param)
                        self.unexpected_files.append(param)
            elif "batch" in cmd:
                if "batch" in cmd:
                    self.locked = True
                    self.queue.append(cmd + "&".join(params))
                    self.locked = False
            elif "failedtosavefile" in cmd:
                self.queue.append("failedtosavefile")
            else:
                self.queue.append(cmd + "&".join(params))

    def set_alert_lostconnection(self, val: bool):
        self.alert_lostconnection = val
