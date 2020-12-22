from tanager_feeder.listeners.listener import Listener
from tanager_feeder import utils

class PiListener(Listener):
    def __init__(self, connection_tracker, test=False):
        super().__init__(connection_tracker)
        self.connection_checker = PiConnectionChecker(None, controller=self.controller, func=self.listen)
        self.local_server = TanagerServer(port=self.connection_tracker.PI_PORT)

        if not self.connection_tracker.pi_offline:
            client = TanagerClient((pi_server_ip, 12345),
                                   'setcontrolserveraddress&' + self.local_server.server_address[0] + '&' + str(
                                       self.connection_tracker.PI_PORT), self.connection_tracker.PI_PORT)
        thread = Thread(target=self.local_server.listen)
        thread.start()

    def send_control_address(self):
        client = TanagerClient((pi_server_ip, 12345),
                               'setcontrolserveraddress&' + self.local_server.server_address[0] + '&' + str(self.connection_tracker.PI_PORT),
                               self.connection_tracker.PI_PORT)

    def run(self):
        i = 0
        while True:
            if not self.connection_tracker.pi_offline and i % 20 == 0:
                connection = self.connection_checker.check_connection(self.connection_tracker.PI_PORT, timeout=8)
                if not connection: self.connection_tracker.pi_offline = True
            else:
                self.listen()
            i += 1
            time.sleep(utils.INTERVAL)

    def listen(self):
        while len(self.local_server.queue) > 0:
            message = self.local_server.queue.pop(0)
            cmd, params = utils.decrypt(message)
            print('Pi read command: ' + cmd)
            self.queue.append(cmd)
