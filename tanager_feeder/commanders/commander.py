from typing import List, Optional

from tanager_feeder.utils import ConnectionManager


class Commander:
    def __init__(self, connection_manager: ConnectionManager, listener):
        self.listener = listener
        self.connection_manager = connection_manager

    def send(self, message: str):
        raise NotImplementedError

    def remove_from_listener_queue(self, commands: List):
        for command in commands:
            while command in self.listener.queue:
                self.listener.queue.remove(command)

        extended_commands = [
            "spec_data",
            "log_data",
            "donemoving",
            "currentposition",
        ]
        for command in commands:
            if command in extended_commands:
                for item in self.listener.queue:
                    if command in item:
                        self.listener.queue.remove(item)

    @staticmethod
    def encrypt(cmd: str, parameters: Optional[List] = None):
        if parameters is None:
            parameters = []
        filename = cmd
        for param in parameters:
            param = str(param)
            param = param.replace("/", "+")
            param = param.replace("\\", "+")
            param = param.replace(":", "=")
            filename = filename + "&" + param
        return filename
