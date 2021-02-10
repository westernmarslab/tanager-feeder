from threading import Thread
import time

from tanager_feeder.listeners.listener import Listener
from tanager_feeder import utils
from tanager_feeder.connection_checkers.spec_connection_checker import SpecConnectionChecker
from tanager_tcp import TanagerClient
from tanager_tcp import TanagerServer


class SpecListener(Listener):
    def __init__(self, connection_tracker, config_info):
        super().__init__(connection_tracker, config_info)
        self.connection_checker = SpecConnectionChecker(connection_tracker, config_info, func=self.listen)
        self.unexpected_files = []
        self.wait_for_unexpected_count = 0
        self.alert_lostconnection = True
        self.new_dialogs = True
        self.local_server = TanagerServer(port=self.connection_tracker.SPEC_PORT)
        if not self.connection_tracker.spec_offline:
            client = TanagerClient(
                (self.connection_tracker.spec_ip, 12345),
                "setcontrolserveraddress&"
                + self.local_server.server_address[0]
                + "&"
                + str(self.connection_tracker.SPEC_PORT),
                self.connection_tracker.SPEC_PORT,
            )
        thread = Thread(target=self.local_server.listen)
        thread.start()

    def set_control_address(self):
        client = TanagerClient(
            (spec_server_ip, 12345),
            "setcontrolserveraddress&"
            + self.local_server.server_address[0]
            + "&"
            + str(self.connection_tracker.SPEC_PORT),
            self.connection_tracker.SPEC_PORT,
        )

    def run(self):
        i = 0
        while True:
            if not self.connection_tracker.spec_offline and i % 20 == 0:
                connection = self.connection_checker.check_connection(timeout=8)
                if not connection:
                    self.connection_tracker.spec_offline = True
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

            elif "lostconnection" in cmd:
                if self.alert_lostconnection:
                    print("Spec read command: lostconnection")
                    self.alert_lostconnection = False

                    buttons = {
                        "retry": {
                            self.set_alert_lostconnection: [True],
                        },
                        "work offline": {},
                        "exit": {exit_func: []},
                    }
                    try:
                        dialog = ErrorDialog(
                            controller=self.controller,
                            title="Lost Connection",
                            label="Error: RS3 has no connection with the spectrometer.\nCheck that the spectrometer is"
                                  " on.\n\nNote that RS3 can take some time to connect to the spectrometer.\nBe patient"
                                  " and wait for the dot at the lower right of RS3 to turn green.",
                            buttons=buttons,
                            button_width=15,
                            width=600,
                        )
                    except:
                        print("Ignoring an error in Listener when I make a new error dialog")

            elif "unexpectedfile" in cmd:
                if self.new_dialogs:
                    try:
                        dialog = ErrorDialog(
                            self.controller,
                            title="Untracked Files",
                            label="There is an untracked file in the data directory.\nDoes this belong here?\n\n"
                            + params[0],
                        )
                    except:
                        print("Ignoring an error in Listener when I make a new error dialog")
                else:
                    self.unexpected_files.append(params[0])

            else:
                self.queue.append(cmd)

    def set_alert_lostconnection(self, bool):
        self.alert_lostconnection = bool
