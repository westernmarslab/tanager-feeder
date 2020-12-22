from tanager_feeder.listeners.listener import Listener

class PiListener(Listener):
    def __init__(self, pi_server_ip, test=False):
        super().__init__(pi_server_ip, PI_OFFLINE)
        self.connection_checker = PiConnectionChecker(None, controller=self.controller, func=self.listen)
        self.local_server = TanagerServer(port=PI_PORT)
        if not PI_OFFLINE:
            client = TanagerClient((pi_server_ip, 12345),
                                   'setcontrolserveraddress&' + self.local_server.server_address[0] + '&' + str(
                                       PI_PORT), PI_PORT)
        thread = Thread(target=self.local_server.listen)
        thread.start()

    def send_control_address(self):
        client = TanagerClient((pi_server_ip, 12345),
                               'setcontrolserveraddress&' + self.local_server.server_address[0] + '&' + str(PI_PORT),
                               PI_PORT)

    def run(self):
        i = 0
        global PI_OFFLINE  # no idea why this declaration is needed, I'm not modifying the value of PI_OFFLINE, but I am getting an unbound local variable error.
        while True:
            if not PI_OFFLINE and i % 20 == 0:
                connection = self.connection_checker.check_connection(PI_PORT, timeout=8)
                if not connection: PI_OFFLINE = True
            else:
                self.listen()
            i += 1
            time.sleep(INTERVAL)

    def listen(self):
        while len(self.local_server.queue) > 0:
            message = self.local_server.queue.pop(0)
            cmd, params = decrypt(message)
            print('Pi read command: ' + cmd)

            self.queue.append(cmd)