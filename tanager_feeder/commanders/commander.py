from typing import List, Optional

from tanager_tcp import TanagerClient


class Commander:
    def __init__(self, remote_server_ip: str, listener):
        self.listener = listener
        self.remote_server_ip = remote_server_ip

    def send(self, filename: str, listening_port: int, offline: bool):
        if offline:
            return False

        try:
            # TODO: don't make a new client each time, invoke client's send method instead.
            TanagerClient((self.remote_server_ip, 12345), filename, listening_port)
            return True
        # pylint: disable=broad-except
        except Exception as e:
            # TODO: Figure out what kind of exception this could be
            print(e)
            print("ERROR: Could not send message.")
            return False

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
