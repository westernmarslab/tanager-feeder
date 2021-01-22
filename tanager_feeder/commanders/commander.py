from tanager_tcp import TanagerClient
from tanager_tcp import TanagerServer


class Commander:
    def __init__(self, remote_server_ip, listener):
        self.listener = listener
        self.remote_server_ip = remote_server_ip

    def send(self, filename, listening_port, offline):
        if offline:
            return False
        else:
            client = TanagerClient((self.remote_server_ip, 12345), filename, listening_port)
            return True

    def remove_from_listener_queue(self, commands):
        for command in commands:
            while command in self.listener.queue:
                self.listener.queue.remove(command)

        for command in commands:
            if command == "spec_data":
                for item in self.listener.queue:
                    if "spec_data" in item:
                        self.listener.queue.remove(item)

            if command == "log_data":
                for item in self.listener.queue:
                    if "log_data" in item:
                        self.listener.queue.remove(item)

            if command == "donemoving":
                for item in self.listener.queue:
                    if "donemoving" in item:
                        self.listener.queue.remove(item)

            if command == "currentposition":
                for item in self.listener.queue:
                    if "currentposition" in item:
                        self.listener.queue.remove(item)

    def encrypt(self, cmd, parameters=[]):
        filename = cmd
        for param in parameters:
            param = str(param)
            param = param.replace("/", "+")
            param = param.replace("\\", "+")
            param = param.replace(":", "=")
            filename = filename + "&" + param
        return filename
