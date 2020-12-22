from threading import Thread

class Listener(Thread):
    def __init__(self, connection_tracker, test=False):
        Thread.__init__(self)
        self.connection_tracker = connection_tracker
        self.controller = None
        self.queue = []

    def run(self):
        i = 0
        while True:
            if not self.connection_tracker.offline and i % 20 == 0:
                print('check')
                connection = self.connection_checker.check_connection(timeout=8)

            else:
                self.listen()
            i += 1
            time.sleep(INTERVAL)

    def listen(self):
        pass

    def set_controller(self, controller):
        self.controller = controller
        self.connection_checker.controller = controller