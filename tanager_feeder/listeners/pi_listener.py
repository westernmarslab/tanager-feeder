from threading import Thread
import time

from tanager_tcp.tanager_server import TanagerServer

from tanager_feeder.listeners.listener import Listener
from tanager_feeder import utils
from tanager_feeder.connection_checkers.pi_connection_checker import PiConnectionChecker


class PiListener(Listener):
    def __init__(self, connection_manager: utils.ConnectionManager, config_info: utils.ConfigInfo):
        connection_checker = PiConnectionChecker(connection_manager, config_info, func=self.listen)
        super().__init__(connection_manager, connection_checker)
        self.local_server = TanagerServer(port=self.connection_manager.LISTEN_FOR_PI_PORT)
        self.connection_manager = connection_manager
        self.send_control_address()
        thread = Thread(target=self.local_server.listen)
        thread.start()

    def send_control_address(self):
        self.connection_manager.send_to_pi(
            "setcontrolserveraddress&"
            + self.local_server.server_address[0]
            + "&"
            + str(self.connection_manager.LISTEN_FOR_PI_PORT)
        )

    def run(self):
        i = 0
        while True:
            if not self.connection_manager.pi_offline and i % 100 == 0:
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
            print("Pi read command: " + cmd)
            for param in params:
                cmd += "&" + param
            self.queue.append(cmd)
