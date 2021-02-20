from threading import Thread

from tanager_feeder import utils
from tanager_feeder.connection_checkers.connection_checker import ConnectionChecker


class Listener(Thread):
    def __init__(self, connection_manager: utils.ConnectionManager, connection_checker: ConnectionChecker):
        Thread.__init__(self)
        self.connection_manager = connection_manager
        self.connection_checker = connection_checker
        self.controller = None
        self.queue = []

    def run(self):
        raise NotImplementedError
        # Implementations in subclasses should follow the pattern:
        # i = 0
        # while True:
        #     if not self.connection_manager.offline and i % 20 == 0:
        #         self.connection_checker.check_connection(timeout=8)
        #     else:
        #         self.listen()
        #     i += 1
        #     time.sleep(utils.INTERVAL)

    def listen(self):
        pass

    def set_controller(self, controller):
        self.controller = controller
        self.connection_checker.controller = controller
